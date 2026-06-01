(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",p=s[1]&&s[1].method||"GET",l=String(r).split("?")[0];return o.apply(this,s).then(function(d){const f=Date.now()-i;if(d.ok)f>2500&&a({type:"api_slow",summary:p+" "+l+" → 慢 "+f+"ms",detail:{url:r,method:p,status:d.status,elapsed_ms:f}});else{let c="";try{d.clone().text().then(function(v){c=String(v||"").slice(0,500),a({type:"api_error",summary:p+" "+l+" → "+d.status+" ("+f+"ms)",detail:{url:r,method:p,status:d.status,elapsed_ms:f,body_preview:c}})}).catch(function(){a({type:"api_error",summary:p+" "+l+" → "+d.status+" ("+f+"ms)",detail:{url:r,method:p,status:d.status,elapsed_ms:f,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:p+" "+l+" → "+d.status+" ("+f+"ms)",detail:{url:r,method:p,status:d.status,elapsed_ms:f}})}}return d}).catch(function(d){const f=Date.now()-i;throw a({type:"api_fail",summary:p+" "+l+" → 网络失败 ("+f+"ms)",detail:{url:r,method:p,elapsed_ms:f,error:String(d&&d.message||d)}}),d})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let p=0;p<arguments.length;p++){const l=arguments[p];if(typeof l=="string")r.push(l);else if(l&&l instanceof Error)r.push(l.message);else try{r.push(JSON.stringify(l).slice(0,300))}catch{r.push(String(l))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function En(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function In(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function Bn(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function Xe(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function Ln(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Sn(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function Ze(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function Qe(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function Cn(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...Qe()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")Ze();else{const p=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xe(p),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function Tn(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Qe()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Ze();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xe(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function Mn(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Qe()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Ze();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xe(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=Cn;window.apiPost=Tn;window.t=Xe;window.escapeHtml=Ln;window.svgIcon=Sn;window._showSessionRevokedModal=Ze;window._wsHeader=Qe;window.apiPut=Mn;window.getMaxFiles=En;window.getMaxPagesPerFile=In;window.getMaxMbPerFile=Bn;function gt(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&yt(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function $n(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});$n("lang-dropdown",e=>gt(e.dataset.lang));const Pt=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function Dt(e){Pt.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function qt(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function yt(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function Rt(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),qt(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}yt(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}function Hn(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.applyLang=gt;window.routeTo=Dt;window.loadAll=Rt;window.renderBrandWorkspace=qt;window.updateUploadHint=yt;window.installNetworkBanner=Hn;try{gt(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");Dt(Pt.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);Rt();const Ft="mrpilot_sidebar_collapsed";localStorage.getItem(Ft)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(Ft,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),p=document.getElementById("int-drawer-body");if(!s||!p)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),p.innerHTML="";var l={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},d=l[a]||a;const f=document.querySelector('.auto-panel[data-auto-panel="'+d+'"]');f?(f.style.display="block",p.appendChild(f)):p.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var c={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(c[a])try{c[a]()}catch(u){console.warn("[int-drawer] loader error",u)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(u){console.warn("[int-drawer] ERP load error",u)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let Ue=null;function An(){ut(),Ue=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&ut()}catch{}},1e4)}function ut(){Ue&&(clearInterval(Ue),Ue=null)}window.startEnginePolling=An;window.stopEnginePolling=ut;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const Tt=document.getElementById("btn-custom-template");Tt&&Tt.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),p=document.getElementById("pearnly-confirm-cancel"),l=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!p){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function d(b){o.style.display="none",r.removeEventListener("click",f),p.removeEventListener("click",c),l&&l.removeEventListener("click",c),o.removeEventListener("click",u),document.removeEventListener("keydown",v),a(b)}function f(){d(!0)}function c(){d(!1)}function u(b){b.target===o&&d(!1)}function v(b){b.key==="Escape"?d(!1):b.key==="Enter"&&d(!0)}r.addEventListener("click",f),p.addEventListener("click",c),l&&l.addEventListener("click",c),o.addEventListener("click",u),document.addEventListener("keydown",v),setTimeout(function(){try{p.focus()}catch{}},50)})};const jn=`
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

`,Pn=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=jn+Pn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
                            <!-- 批 3 改动 6 (Zihao 2026-05-19 拍板 · v118.34.34) · ERP filter chip ·
                                 按 endpoint_adapter 过滤(mrerp/xero) · FlowAccount 还没上线灰显. -->
                            <span class="erp-logs-filter-sep" aria-hidden="true">|</span>
                            <button class="chip-filter" data-filter-key="adapter" data-filter-val="mrerp"><span data-i18n="erp-logs-filter-mrerp">MR.ERP</span></button>
                            <button class="chip-filter" data-filter-key="adapter" data-filter-val="xero"><span data-i18n="erp-logs-filter-xero">Xero</span></button>
                            <button class="chip-filter chip-filter-disabled" data-filter-key="adapter" data-filter-val="flowaccount" disabled title="即将上线"><span data-i18n="erp-logs-filter-flowaccount">FlowAccount</span> <span class="chip-soon" data-i18n="erp-logs-filter-soon">即将</span></button>
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Dn=`
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

`,qn=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Dn+qn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function Rn(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function Fn(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function zn(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function Nn(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function On(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let p=null;const l=()=>{p&&(clearTimeout(p),p=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(p=setTimeout(l,r)),l}window.showAlert=Rn;window.hideAlerts=Fn;window._humanizeBackendError=zn;window.humanizeError=Nn;window.showToast=On;function Vn(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),p=document.getElementById("confirm-modal-close"),l=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}l.textContent=n.title||t("confirm-default-title");const d=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const v=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),b=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${v}</div>
                <input type="text" id="${d}" placeholder="${b}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const f=v=>{o.style.display="none",i.onclick=null,r.onclick=null,p.onclick=null,o.onclick=null,document.removeEventListener("keydown",u),n.promptInput&&(s.innerHTML=""),r.style.display="",a(v)},c=()=>{const v=d?document.getElementById(d):null;return v?v.value:""},u=v=>{v.key==="Escape"?f(n.promptInput?null:!1):v.key==="Enter"&&f(n.promptInput?c():!0)};i.onclick=()=>f(n.promptInput?c():!0),r.onclick=()=>f(n.promptInput?null:!1),p.onclick=()=>f(n.promptInput?null:!1),o.onclick=v=>{v.target===o&&f(n.promptInput?null:!1)},document.addEventListener("keydown",u),setTimeout(()=>{if(n.promptInput){const v=document.getElementById(d);v&&v.focus()}else i.focus()},50)})}window.showConfirm=Vn;function Un(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof ft=="function"&&ft()}catch(n){console.warn("settings tab side effect failed:",n)}}}function Gn(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function Kn(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function Jn(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function ft(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}Yn(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function Yn(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=Un;window.fillSettingsForms=Gn;window.saveProfile=Kn;window.saveCompany=Jn;window.renderSettings=ft;function et(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function bt(e){return e=e||_userInfo,!!e&&(e.role==="owner"||et(e))}function zt(e){return e=e||_userInfo,!!e&&e.role==="member"&&!et(e)}function Wn(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!et(e)}function Nt(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function Ot(e){return zt(e)}function Xn(e){return bt(e)}function Zn(e){return bt(e)&&Nt(e)}window.isMoneyHidden=Ot;window.isSuperAdmin=et;window.isOwner=bt;window.isEmployee=zt;window.isTrial=Wn;window.isLifetime=Nt;window.shouldHideMoney=Ot;window.canManageTeam=Xn;window.canManageApiKey=Zn;function Qn(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,p;if(o===0)r="danger",p=t("quota-banner-exhausted");else if(s>=90)r="danger",p=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",p=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(p)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const l=e.querySelector(".quota-banner-close");l&&l.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function ea(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const p=document.querySelector('.settings-tab[data-tab="team"]');p&&(p.style.display=a?"":"none");const l=document.querySelector('.settings-panel[data-settings-panel="team"]');l&&(l.dataset.permHidden=a?"0":"1");const d=document.querySelector('.settings-tab[data-tab="api"]');d&&(d.style.display=o||isSuperAdmin(e)?"":"none");const f=document.querySelector('.settings-tab[data-tab="plan"]');f&&(f.style.display=n?"none":"");const c=document.querySelector('.settings-tab[data-tab="company"]');c&&(c.style.display=n?"none":"");const u=document.getElementById("info-bar");u&&(u.style.display=n?"none":"");const v=document.getElementById("trial-banner");v&&n&&(v.style.display="none");const b=document.getElementById("plan-banner");b&&n&&(b.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(C=>{C.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const C=document.querySelector(".settings-tab.active");C&&C.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(C){console.warn("[v118.12.3] failed to fix active tab:",C)}if(window.PEARNLY_ADMIN_MODE){const C=document.getElementById("admin-mode-banner");C&&(C.style.display="flex"),document.querySelectorAll(".nav-item").forEach(h=>{h.classList.contains("nav-admin-only")||(h.style.display="none")}),document.querySelectorAll(".nav-group").forEach(h=>{h.classList.contains("nav-group-admin-only")||(h.style.display="none")});const E=document.getElementById("client-switcher");E&&(E.style.display="none"),document.body.classList.add("admin-mode");const m=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(h=>{const M=h.dataset.tab;M&&!m.includes(M)&&(h.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(h=>{const M=h.dataset.pane;M&&!m.includes(M)&&(h.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(h=>{const M=h.querySelectorAll(".settings-tab");Array.from(M).some(P=>P.style.display!=="none")||(h.style.display="none")})}}function ta(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Qn;window.applySidebarVisibility=ea;window.renderInfoBar=ta;async function Vt(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function Ut(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Ke(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Se(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function na(e){const a=Ke(e==="seller"?"seller_tax":"buyer_tax");Se(e,t("rd-verifying"),"loading");const o=await Vt("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Se(e,t(Ut(o.error)),"error");return}o.data&&o.data.valid?Se(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Se(e,t("rd-status-invalid"),"invalid")}async function aa(e){const a=Ke(e==="seller"?"seller_tax":"buyer_tax");Se(e,t("rd-syncing"),"loading");const o=await Vt("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Se(e,t(Ut(o.error)),"error");return}Se(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),oa(e,o.data)}}function oa(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Ke(a),i=Ke(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const p=[];n.branch_label&&p.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&p.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let l=document.getElementById("rd-sync-modal");if(l||(l=document.createElement("div"),l.id="rd-sync-modal",l.className="rd-modal-mask",document.body.appendChild(l)),r.length===0)l.innerHTML=`
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
        `}l.classList.add("show");const d=()=>l.classList.remove("show");l.querySelector(".rd-modal-close").addEventListener("click",d),l.querySelectorAll("[data-rd-modal-close]").forEach(c=>c.addEventListener("click",d)),l.addEventListener("click",c=>{c.target===l&&d()});const f=l.querySelector("[data-rd-modal-apply]");f&&f.addEventListener("click",()=>{const c=_results[_drawerIdx];if(!c){d();return}l.querySelectorAll("[data-rd-apply]:checked").forEach(u=>{const v=u.dataset.field,b=u.dataset.value;c.edits[v]=b,c.merged_fields[v]=b;const C=document.querySelector(`[data-field="${v}"]`);C&&(C.value=b);const E=document.querySelector(`[data-field-wrap="${v}"]`);E&&E.classList.add("edited")}),updateDrawerEditCount(),renderResults(),d()})}window.callRdVerify=na;window.callRdSync=aa;function sa(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function ia(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),Gt(),renderResults()}function Gt(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=sa;window.onFieldEdit=ia;window.updateDrawerEditCount=Gt;function ra(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),p=await r.json().catch(()=>({}));if(!r.ok){const l=p&&p.detail||"unknown",d={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=d[l]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=ra;(function(){let e=null,n=null,a=null,o=null;function s(h){return document.getElementById(h)}async function i(){b(),E(),await r()}async function r(){try{const h=localStorage.getItem("mrpilot_token"),M=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!M.ok){C(t("linebot-err-status"));return}const B=await M.json();B.bound?p(B):await l()}catch{C(t("linebot-err-status"))}}function p(h){v(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const M=s("linebot-status-summary");M&&(M.textContent=t("linebot-status-bound"),M.style.background="#D1FAE5",M.style.color="#065F46");const B=s("linebot-bound-name");B&&(B.textContent=h.line_display_name||"(LINE User)");const P=s("linebot-avatar");P&&(h.line_picture_url?(P.src=h.line_picture_url,P.style.display=""):P.style.display="none");const H=s("linebot-bound-since");H&&h.bound_at&&(H.textContent=new Date(h.bound_at).toLocaleString())}async function l(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const h=s("linebot-status-summary");h&&(h.textContent=t("linebot-status-unbound"),h.style.background="#FEE2E2",h.style.color="#B91C1C"),await d(),u()}async function d(){try{const h=localStorage.getItem("mrpilot_token"),M=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+h}});if(!M.ok){C(t("linebot-err-code"));return}const B=await M.json();a=B.code,o=new Date(B.expires_at).getTime(),f(B)}catch{C(t("linebot-err-code"))}}function f(h){const M=s("linebot-code");M&&(M.textContent=h.code);const B=s("linebot-bot-id");B&&(B.textContent=h.bot_basic_id||t("linebot-bot-id-missing"));const P=s("linebot-qr");if(P)if(h.bot_friend_url){const H="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(h.bot_friend_url);P.classList.remove("empty"),P.innerHTML='<img src="'+H+'" alt="LINE Bot QR">'}else P.classList.add("empty"),P.innerHTML="";c()}function c(){e&&clearInterval(e);const h=s("linebot-code-expires");function M(){if(!o)return;const B=o-Date.now();if(B<=0){h&&(h.textContent=t("linebot-code-expired"),h.classList.add("expiring"));const g=s("linebot-code");g&&(g.style.opacity="0.4"),clearInterval(e),e=null;return}const P=Math.floor(B/1e3),H=Math.floor(P/60),_=P%60;h&&(h.textContent=t("linebot-code-expires-in").replace("{m}",H).replace("{s}",String(_).padStart(2,"0")),B<6e4?h.classList.add("expiring"):h.classList.remove("expiring"))}M(),e=setInterval(M,1e3)}function u(){v(),n=setInterval(async()=>{try{const h=localStorage.getItem("mrpilot_token"),M=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+h}});if(!M.ok)return;const B=await M.json();B.bound&&p(B)}catch{}},4e3)}function v(){n&&(clearInterval(n),n=null)}function b(){e&&(clearInterval(e),e=null),v()}function C(h){const M=s("linebot-error");M&&(M.textContent=h,M.style.display="block")}function E(){const h=s("linebot-error");h&&(h.style.display="none")}async function m(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const M=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+M}})).ok){C(t("linebot-err-unbind"));return}await i()}catch{C(t("linebot-err-unbind"))}}document.addEventListener("click",h=>{if(h.target.closest("#linebot-code-refresh")){h.preventDefault(),E(),d();return}if(h.target.closest("#linebot-unbind")){h.preventDefault(),m();return}}),window._loadLineBotPanel=i})();function nt(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const p=parseFloat(r.merged_fields.total_amount);isNaN(p)||(n+=p)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,p)=>({...r,_idx:p}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(p=>(p.filename||"").toLowerCase().includes(r)||(p.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,p)=>{let l,d;return _sortKey==="filename"?(l=r.filename,d=p.filename):_sortKey==="invoice_no"?(l=r.merged_fields.invoice_number,d=p.merged_fields.invoice_number):_sortKey==="invoice_date"?(l=r.merged_fields.date,d=p.merged_fields.date):_sortKey==="total"?(l=parseFloat(r.merged_fields.total_amount)||0,d=parseFloat(p.merged_fields.total_amount)||0):_sortKey==="confidence"?(l=r.confidence,d=p.confidence):(l="",d=""),l<d?_sortDir==="asc"?-1:1:l>d?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,p)=>{const l=r.merged_fields,d=`<span class="empty-cell">${t("empty-val")}</span>`,f="conf-tip-"+(r.confidence||"low"),c="conf-"+(r.confidence||"low"),u=t(f),v=t(c);return`
            <tr data-idx="${r._idx}">
                <td class="num">${p+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${l.invoice_number?escapeHtml(l.invoice_number):d}</td>
                <td class="date">${l.date?escapeHtml(l.date):d}</td>
                <td class="amount">${l.total_amount?Number(l.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):d}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(u)}">${v}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const p=parseInt(r.dataset.idx,10);Jt(p)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),nt()})});let Mt=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout(Mt),Mt=setTimeout(()=>{_searchKeyword=n.trim(),nt(),Kt()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",nt(),Kt(),e.focus()});function Kt(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function Jt(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
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
            ${be("invoice_number","drawer-lbl-invoice",r.invoice_number,"input",s)}
            ${be("date","drawer-lbl-date",r.date,"input",s)}
            ${r.date_raw&&r.date_raw!==r.date?`<div class="date-raw-hint" title="${escapeHtml(t("drawer-date-raw-tip"))}">${escapeHtml(t("drawer-date-raw-label"))}: ${escapeHtml(r.date_raw)}</div>`:""}
            ${be("subtotal","drawer-lbl-subtotal",r.subtotal,"input",s)}
            ${be("vat","drawer-lbl-vat",r.vat,"input",s)}
            ${be("total_amount","drawer-lbl-total",r.total_amount,"input",s)}
            ${r.wht_amount||r.wht_rate?`
                ${be("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,la(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${be("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${be("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,d,$t("seller"))}
            ${be("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${be("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${be("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,d,$t("buyer"))}
            ${be("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?ca(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${be("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(f=>`--- Page ${f.page||f.page_number||"?"} ---
${f.raw_text||f.text||""}`).join(`

`))}</pre>
        </details>
    `,s?p.querySelectorAll("[data-field]").forEach(f=>{f.addEventListener("input",onFieldEdit)}):p.querySelectorAll("[data-field]").forEach(f=>{f.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const f=n._historyId||n.history_id||null;window.bindDrawerClient(f,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const f=document.getElementById("drawer-cat-input");f&&!f.value&&!f.readOnly&&f.focus()},80)}function la(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function be(e,n,a,o,s,i,r){const p=_results[_drawerIdx],l=p&&p.edits[e]!==void 0?p.edits[e]:a,d=p&&p.edits[e]!==void 0&&p.edits[e]!==a,f=escapeHtml(l??""),c=s?"":"readonly",u=o==="textarea"?`<textarea data-field="${e}" rows="2">${f}</textarea>`:`<input type="text" data-field="${e}" value="${f}">`;return`
        <div class="drawer-field ${d?"edited":""} ${c}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${u}
        </div>
    `}function $t(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function ca(e){return`
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
    `}function da(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=nt;window.openDrawer=Jt;window.closeDrawer=da;function pa(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(p){return p&&p.enabled!==!1&&(p.adapter||"").toLowerCase()!=="mrerp_dms"});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const p=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:p}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(p){p.preventDefault(),p.stopPropagation(),o.length===1?Yt(n,o[0].id):ua(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function ua(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(l=>l.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(l){const d=escapeHtml(l.name||l.adapter||"ERP"),f=escapeHtml((l.adapter||"").toLowerCase()),u=l.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(l.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+f+"</span>"+d+u+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",p,!0)},p=l=>{!s.contains(l.target)&&l.target!==e&&!e.contains(l.target)&&r()};setTimeout(()=>document.addEventListener("click",p,!0),0),s.addEventListener("click",l=>{const d=l.target.closest("[data-ep-id]");if(!d)return;const f=d.getAttribute("data-ep-id");r(),Yt(n,f)})}async function Yt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=pa;const fa=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Wt(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function ma(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Xt(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const d=[];for(const f of _results){const c=f.invoices&&f.invoices.length>0?f.invoices:null;if(c&&c.length>1)for(let u=0;u<c.length;u++){const v=c[u]||{};d.push({filename:f.filename+" #"+(u+1)+"/"+c.length,engine:f.engine,merged_fields:v.fields||{}})}else d.push({filename:f.filename,engine:f.engine,merged_fields:f.merged_fields})}a=await apiPost("/api/ocr/export",{records:d,lang:currentLang,template:"sales_detail_th"})}else{const d=[];for(const c of _results)c.history_ids&&Array.isArray(c.history_ids)?d.push(...c.history_ids):c.history_id&&d.push(c.history_id);if(d.length===0){showToast(t("toast-export-error"),"error");return}const f=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+f,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:d,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let d="HTTP "+a.status;try{const c=await a.json();c&&c.detail&&(d=typeof c.detail=="string"?c.detail:JSON.stringify(c.detail))}catch(c){console.warn("[export] resp.json err.detail parse failed:",c)}const f=typeof d=="string"&&d.indexOf(".")>0?"err."+d:null;showToast(f?t(f):t("toast-export-error")+" · "+d,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const f=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(f)try{i=decodeURIComponent(f[1])}catch{}}const p=URL.createObjectURL(s),l=document.createElement("a");l.href=p,l.download=i,document.body.appendChild(l),l.click(),document.body.removeChild(l),URL.revokeObjectURL(p),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Xt(Wt())});function va(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Wt(),o=fa.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function dt(){const e=document.getElementById("export-dropdown");e&&e.remove()}const pt=document.getElementById("btn-export-arrow");pt&&pt.addEventListener("click",e=>{e.stopPropagation(),!pt.disabled&&va()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){dt(),showToast(t("cs-coming-soon"),"info");return}ma(a),dt(),Xt(a);return}e.target.closest("#btn-export-arrow")||dt()});function ha(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(ha,300);function wt(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function ga(){_historySelected.clear(),wt()}async function _t(){if(!_userInfo){setTimeout(()=>_t(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const d=await r.json().catch(()=>({}));if((typeof d.detail=="string"?d.detail:d.detail&&d.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const p=await r.json();_historyState.items=p.items||[],_historyState.total=p.total||0;const l=new Set(_historyState.items.map(d=>d.id));for(const d of Array.from(_historySelected))l.has(d)||_historySelected.delete(d);Zt()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function Zt(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(d=>{d.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(d=>{const f=new Date(d.created_at),c=String(f.getMonth()+1).padStart(2,"0"),u=String(f.getDate()).padStart(2,"0"),v=String(f.getHours()).padStart(2,"0"),b=String(f.getMinutes()).padStart(2,"0"),C=`${c}-${u} ${v}:${b}`,E=escapeHtml(d.filename||""),m=E.length>50?E.substring(0,50)+"…":E,h=d.invoice_no?escapeHtml(d.invoice_no):m,M=[];d.seller_name&&M.push(escapeHtml(d.seller_name)),d.invoice_no&&d.filename&&M.push(m);const B=M.join(" · ")||"-",P=d.category_tag?`<span class="history-badge category">${escapeHtml(d.category_tag)}</span>`:"",H=d.source_total&&d.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:d.source_index||1,n:d.source_total}))}</span>`:"",_=d.total_amount!==null&&d.total_amount!==void 0?Number(d.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',g=[];(d.total_amount===null||d.total_amount===void 0)&&g.push(t("field-amount")),d.invoice_no||g.push(t("field-invoice-no")),d.invoice_date||g.push(t("field-invoice-date")),d.seller_name||g.push(t("field-seller-name")),g.length>0&&`${escapeHtml(d.id)}${escapeHtml(t("history-needs-review-tip")+" · "+g.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,d.edited&&`${escapeHtml(t("history-edited",{n:d.edit_count||1}))}`;const k=d.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",S=d.confidence==="high"?"high":d.confidence==="medium"?"mid":"low",T=d.confidence==="high"?t("conf-high"):d.confidence==="medium"?t("conf-medium"):t("conf-low"),q=`<span class="history-badge conf-${S}">${escapeHtml(T)}</span>`;let L="";const D=d.source||"manual";return D==="email"?L=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:D==="folder"?L=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:D==="api"&&(L=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(d.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(d.id)}" ${_historySelected.has(d.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${C}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${h} ${P} ${H} ${L} ${k}</div>
                        <div class="history-cell-subtitle">${B}</div>
                    </div>
                    <div class="history-cell-amount">${_}</div>
                    <div class="history-cell-conf">${q}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(d.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),wt();const p=a.length>0?_historyState.page*_historyState.pageSize+1:0,l=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:p,to:l,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=_t;window.renderHistoryList=Zt;window.updateHistoryBatchBar=wt;window.clearHistorySelection=ga;typeof currentRoute<"u"&&currentRoute==="history"&&_t();async function Je(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),ba(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),wa(a.id)}catch(n){console.error("open history detail failed",n)}}async function ya(e){await Je(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function ba(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",ka),document.getElementById("btn-push-erp").addEventListener("click",_a)}async function wa(e){}async function _a(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function ka(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(p=>!p.is_duplicate&&!p.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function xa(e,n){document.querySelectorAll(".history-popover").forEach(d=>d.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(d=>d.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const p=()=>{r.remove(),document.removeEventListener("click",l,!0)},l=d=>{!r.contains(d.target)&&d.target!==n&&p()};setTimeout(()=>document.addEventListener("click",l,!0),0),r.addEventListener("click",async d=>{const f=d.target.closest("[data-act]");if(!f||f.disabled)return;const c=f.dataset.act;if(p(),c==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const v=document.createElement("textarea");v.value=s,v.style.position="fixed",v.style.opacity="0",document.body.appendChild(v),v.select(),document.execCommand("copy"),document.body.removeChild(v),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(c==="download-pdf"){const u=showToast(t("history-download-pdf-loading"),"loading",0);try{const v=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!v.ok)throw new Error("download failed");const b=await v.blob(),C=URL.createObjectURL(b),E=document.createElement("a");E.href=C,E.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(E),E.click(),document.body.removeChild(E),setTimeout(()=>URL.revokeObjectURL(C),5e3),u(),showToast(t("history-download-pdf-ok"),"success")}catch{u(),showToast(t("history-download-pdf-fail"),"error")}}else if(c==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const p=r.target.closest(".history-row"),l=r.target.closest("[data-hmenu]");if(l){r.stopPropagation(),xa(l.dataset.hmenu,l);return}const d=r.target.closest("[data-review]");if(d){r.stopPropagation(),Je(d.dataset.review);return}const f=r.target.closest("[data-fill-amount]");if(f){r.stopPropagation(),ya(f.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||p&&!r.target.closest("[data-hmenu]")&&Je(p.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const p=r.target.closest(".history-row-check");if(!p)return;const l=p.dataset.hid;p.checked?_historySelected.add(l):_historySelected.delete(l),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const p=r.target.checked;for(const l of _historyState.items)p?_historySelected.add(l.id):_historySelected.delete(l.id);document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=p}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const l=Array.from(_historySelected);try{const d=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:l})});if(!d.ok)throw new Error("batch delete failed");const f=await d.json();showToast(t("history-batch-done",{n:f.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(d){console.error("batch delete",d),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const p=r.target.value;document.getElementById("history-search-clear").style.display=p?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=p.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Je;const $e=document.getElementById("drop-zone"),kt=document.getElementById("file-input");$e.addEventListener("click",()=>kt.click());kt.addEventListener("change",e=>Qt(e.target.files));["dragover","dragenter"].forEach(e=>{$e.addEventListener(e,n=>{n.preventDefault(),$e.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{$e.addEventListener(e,n=>{n.preventDefault(),$e.classList.remove("drag-over")})});$e.addEventListener("drop",e=>{e.preventDefault(),Qt(e.dataTransfer.files)});const Ea=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function mt(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function Ia(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function Ba(e){return Ia(e)||mt(e)||Ea.test(e.name)}function Qt(e){hideAlerts();const n=Array.from(e),a=n.filter(Ba);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(p=>!mt(p)),s=a.filter(mt),i=new Set(_selectedFiles.map(p=>p.name+"_"+p.size));for(const p of o){const l=p.name+"_"+p.size;i.has(l)||(_selectedFiles.push({file:p,name:p.name,size:p.size,status:"waiting",errorKey:null,errorParams:null}),i.add(l))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(p){console.error("[upload] image route failed",p)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),at(),xt(),kt.value=""}let Ve=!1;function at(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(c=>c.status==="processing"||c.status==="retrying").length,o=_selectedFiles.filter(c=>c.status==="success").length,s=_selectedFiles.filter(c=>c.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const p=Ve?t("file-list-collapse"):t("file-list-expand"),l=_selectedFiles.map((c,u)=>{let v=t("status-"+c.status);c.status==="retrying"&&(v=t("status-retrying")),c.status==="error"&&c.errorKey&&(v=t(c.errorKey,c.errorParams||{}));const b=c.status==="processing"||c.status==="retrying"?'<span class="spinner"></span>':"",C=c.status==="error"&&c.canRetry?`<button class="file-retry-btn" data-retry-idx="${u}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",E=c.status==="success"&&c.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                ${E}
                <span class="file-status ${c.status}">${b}${v}</span>
                ${C}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(p)}</button>`:""}
        </div>
        <ul class="file-list-body${Ve?" expanded":""}" id="file-list-body">
            ${l}
        </ul>
    `;const d=document.getElementById("file-list-toggle");d&&d.addEventListener("click",()=>{Ve=!Ve,at()});const f=document.getElementById("file-list-body");f&&!f.dataset.retryBound&&(f.dataset.retryBound="1",f.addEventListener("click",async c=>{const u=c.target.closest(".file-retry-btn");if(!u)return;const v=parseInt(u.dataset.retryIdx||"-1",10);if(v<0||v>=_selectedFiles.length)return;const b=_selectedFiles[v];!b||b.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(b,!0)}))}function xt(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],at(),renderResults(),xt(),hideAlerts()});window.renderFileList=at;window.updateStartButton=xt;(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await Sa()||o.click()}),o.addEventListener("change",async p=>{const l=Array.from(p.target.files||[]);if(p.target.value="",l.length!==0)for(const d of l)await vt([d],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=p=>async l=>{const d=Array.from(l.target.files||[]);if(l.target.value="",d.length===0)return;const f=d.filter(u=>u.type==="application/pdf"||/\.pdf$/i.test(u.name)),c=d.filter(u=>!f.includes(u));f.length>0&&await La(f),c.length>0&&await vt(c,p)};a&&a.addEventListener("change",r("gallery"))})();async function La(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function Sa(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=p=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(p)},r=p=>{p.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=p=>{p.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}async function Ye(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const p=document.createElement("canvas");p.width=64,p.height=64;const l=p.getContext("2d");l.drawImage(o,0,0,64,64);const d=l.getImageData(0,0,64,64).data;let f=0,c=0;for(let v=0;v<d.length;v+=4)f+=.299*d[v]+.587*d[v+1]+.114*d[v+2],c++;const u=c?f/c:128;u<70?s.push("too_dark"):u>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:u})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}let _e=[],Le=null;async function vt(e,n){if(hideAlerts(),!(!e||e.length===0)){var a=typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice";if(a==="thai_id_card"){for(const s of e)_selectedFiles.push({file:s,name:s.name,size:s.size,status:"waiting",errorKey:null,errorParams:null});const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton();return}if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let o=0;o<30&&(await new Promise(s=>setTimeout(s,100)),!(window.jspdf&&window.jspdf.jsPDF));o++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const o=e[0];let s={};try{s=await Ye(o)}catch{}_e.push({file:o,quality:s}),Le="camera",Me();return}if(n==="gallery"&&(e.length>=2||_e.length>0)){for(const o of e){let s={};try{s=await Ye(o)}catch{}_e.push({file:o,quality:s})}Le="gallery",Me();return}await en(e)}}async function Ca(e){const n=new Set;for(const o of e)try{((await Ye(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await tn(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function Me(){let e=document.getElementById("camera-buffer-bar");if(_e.length===0){e&&e.remove(),Le=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=_e.length,a=n>=2,o=Le==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{_e=[],Le=null,Me()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const l=o?"gallery-input":"camera-input",d=document.getElementById(l);d&&d.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const l=_e.map(d=>d.file);_e=[],Le=null,Me(),await Ca(l)});const p=e.querySelector('[data-cbb-action="separate"]');p&&(p.onclick=async()=>{const l=_e.map(d=>d.file);_e=[],Le=null,Me(),await en(l)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{_e.length>0&&Me()});async function en(e){const n=new Set;let a=0;for(const s of e)try{((await Ye(s)).warnings||[]).forEach(p=>n.add(p));const r=await tn([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}async function tn(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let d=0;d<e.length;d++){const f=e[d],{dataUrl:c,naturalW:u,naturalH:v}=await Ta(f);d>0&&s.addPage("a4","p");const b=u/v;let C=a-10,E=C/b;E>o-10&&(E=o-10,C=E*b);const m=(a-C)/2,h=(o-E)/2,M=f.type==="image/png"?"PNG":"JPEG";s.addImage(c,M,m,h,C,E,void 0,"FAST")}const i=s.output("blob"),r=new Date,p=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),l=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${p}${l}.pdf`,{type:"application/pdf"})}function Ta(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}window.handleCameraImages=vt;(function(){var e="pearnly_ocr_doc_mode",n=!1,a=!1;function o(u){return typeof escapeHtml=="function"?escapeHtml(u==null?"":String(u)):String(u??"")}function s(){try{return localStorage.getItem(e)==="thai_id_card"?"thai_id_card":"invoice"}catch{return"invoice"}}window.getOcrDocumentMode=function(){return n?s():"invoice"};function i(){var u=document.getElementById("drop-zone");return u?u.closest(".card"):null}function r(){var u=i();if(!u)return null;var v=u.querySelector("#ocr-doc-mode");if(v)return v;var b=u.querySelector(".section-head");return v=document.createElement("div"),v.id="ocr-doc-mode",v.className="ocr-doc-mode",v.setAttribute("role","tablist"),v.style.cssText="display:none;gap:6px;margin:0 0 14px;padding:4px;border-radius:10px;background:var(--bg,#f5f5f3);border:1px solid var(--line,#e5e5e0);width:fit-content;",b&&b.parentNode?b.parentNode.insertBefore(v,b.nextSibling):u.insertBefore(v,u.firstChild),v}function p(u,v,b){return'<button type="button" class="ocr-doc-seg'+(b?" active":"")+'" data-doc-mode="'+u+'" role="tab" aria-selected="'+(b?"true":"false")+'" style="border:none;background:'+(b?"var(--card,#fff)":"transparent")+";color:var(--ink,#1a1a1a);font:inherit;font-size:13px;font-weight:"+(b?"600":"500")+";padding:6px 16px;border-radius:7px;cursor:pointer;box-shadow:"+(b?"0 1px 3px rgba(0,0,0,.08)":"none")+';transition:background .15s;">'+o(t(v))+"</button>"}function l(){var u=r();if(u){if(!n){u.style.display="none";return}var v=s();u.style.display="flex",u.innerHTML=p("invoice","ocr-mode-invoice",v==="invoice")+p("thai_id_card","ocr-mode-id-card",v==="thai_id_card")}}function d(u){try{localStorage.setItem(e,u==="thai_id_card"?"thai_id_card":"invoice")}catch{}l();try{document.dispatchEvent(new CustomEvent("ocr-doc-mode-change",{detail:{mode:window.getOcrDocumentMode()}}))}catch{}}async function f(u){if(!(a&&!u)){var v=localStorage.getItem("mrpilot_token");if(v)try{var b=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+v}});if(!b.ok)return;var C=await b.json(),E=C&&C.items||[];n=E.some(function(m){return m&&(m.adapter||"").toLowerCase()==="mrerp_dms"&&m.enabled!==!1}),a=!0,window._dmsHasEndpoint=n,l()}catch{}}}window._refreshOcrDocMode=function(){f(!0)},document.addEventListener("click",function(u){var v=u.target.closest(".ocr-doc-seg");v&&v.getAttribute("data-doc-mode")&&(u.preventDefault(),d(v.getAttribute("data-doc-mode")))}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("ocr-doc-mode",l);function c(){r(),l(),f(!1)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),window.addEventListener("hashchange",function(){((location.hash||"").indexOf("ocr")>=0||location.hash===""||location.hash==="#home")&&setTimeout(function(){r(),f(!1)},60)})})();(function(){function e(i){return typeof escapeHtml=="function"?escapeHtml(i==null?"":String(i)):String(i??"")}function n(){var i=(function(){var p=document.getElementById("drop-zone");return p?p.closest(".card"):null})();if(!i||!i.parentNode)return null;var r=document.getElementById("dms-id-card-result");return r||(r=document.createElement("div"),r.id="dms-id-card-result",r.className="card",r.style.cssText="display:none;margin-top:16px;",i.parentNode.insertBefore(r,i.nextSibling),r)}function a(i,r){return'<div style="display:flex;justify-content:space-between;gap:16px;padding:8px 0;border-bottom:1px solid var(--line,#eee);"><span style="color:var(--muted,#6b6b66);font-size:13px;">'+e(t(i))+'</span><span style="font-weight:600;font-size:13px;text-align:right;word-break:break-all;">'+e(r||"—")+"</span></div>"}function o(i){if(!i)return"";var r=[i.house_no,i.road,i.subdistrict,i.district,i.province,i.zipcode].filter(function(p){return p});return r.join(" ")||i.address_raw||""}function s(i){var r=i&&i.status||"failed",p,l,d;return r==="success"?(p="#0a7a2c",l="#d6f5e0",d="dms-result-status-success"):r==="needs_review"?(p="#9a6b00",l="#fdf0d0",d="dms-result-status-needs-review"):r==="skipped"?(p="#5d5d57",l="#eee",d="dms-result-status-skipped"):(p="#b3261e",l="#fbe0de",d="dms-result-status-failed"),'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;color:'+p+";background:"+l+';">'+e(t(d))+"</span>"}window.renderDmsIdCardResult=function(i){var r=n();if(r){i=i||{};var p=i.id_card||{},l=p.address||{},d=i.dms_push||{},f=d.status||(i.ok?"success":"failed"),c="";f==="success"&&(c=a("dms-result-customer",d.customer_id)+a("dms-result-booking",d.booking_no));var u=f==="failed"||f==="needs_review"?'<button type="button" class="btn btn-ghost btn-tiny" id="dms-id-card-retry" style="margin-top:12px;">'+e(t("dms-result-retry"))+"</button>":"",v="";if(f==="failed"&&d.error_code){var b="dms-err-"+String(d.error_code).toLowerCase(),C=t(b);(!C||C===b)&&(C=t("dms-err-err_dms_unexpected")),v='<div style="margin-top:8px;color:#b3261e;font-size:12px;">'+e(C)+"</div>"}r.style.display="",r.innerHTML='<div class="section-head" style="display:flex;align-items:center;justify-content:space-between;"><div class="section-title">'+e(t("dms-result-title"))+"</div>"+s(d)+'</div><div style="margin-top:8px;">'+a("dms-result-name",(p.first_name||"")+" "+(p.last_name||""))+a("dms-result-id",p.people_id_masked)+a("dms-result-birthday",p.birthday_be)+a("dms-result-address",o(l))+c+"</div>"+v+u}},window.clearDmsIdCardResult=function(){var i=document.getElementById("dms-id-card-result");i&&(i.style.display="none",i.innerHTML="")},document.addEventListener("click",function(i){i.target.closest("#dms-id-card-retry")&&(i.preventDefault(),typeof window._dmsRetryIdCard=="function"&&window._dmsRetryIdCard())})})();document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,(typeof window.getOcrDocumentMode=="function"?window.getOcrDocumentMode():"invoice")==="thai_id_card"){try{await nn()}finally{const c=document.getElementById("btn-start");c&&(c.disabled=!1)}return}if(_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(u=>u.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const n=_selectedFiles.filter(c=>c.status==="waiting"),a=6;async function o(c,u){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=u?"retrying":"processing",c.canRetry=!1,renderFileList();const v=new AbortController,b=setTimeout(()=>v.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(v);try{const C=new FormData;C.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const B=window.getCurrentClientId();B!=null&&C.append("client_id",String(B))}}catch{}const E=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:C,signal:v.signal});if(clearTimeout(b),window._ocrCtrls.delete(v),E.status===401||E.status===403){const P=await E.clone().json().catch(()=>({})),H=P&&P.detail,_=typeof H=="string"?H:H&&H.code||"";if(!_||_.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),_==="auth.session_revoked")_showSessionRevokedModal();else{const g=_==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(g),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}_==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!E.ok){const P=(await E.json().catch(()=>({}))).detail;return typeof P=="string"?(c.errorKey="err."+P,c.errorParams=null):P&&P.code?(c.errorKey="err."+P.code,c.errorParams={...P,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(E.status===429?c.errorKey="err.rate_limit":E.status===502||E.status===503||E.status===504?c.errorKey="err.gemini_overloaded":E.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const m=await E.json();c.status="success",c.fromCache=!!m.from_cache;const h=mergeFields(m.pages),M=m.confidence||(h.items&&h.items.length>0?"high":"low");if(_results.push({filename:m.filename,pages:m.pages,page_count:m.page_count,elapsed_ms:m.elapsed_ms,engine:m.engine,merged_fields:h,edits:{},confidence:M,history_id:m.history_id,history_ids:m.history_ids||[],invoice_count:m.invoice_count||1,invoices:m.invoices||[],archive_name:m.archive_name||null,category_tag:m.category_tag||null,auto_pushed:!!m.auto_pushed,typhoon_enhanced:!!m.typhoon_enhanced,typhoon_pages:m.typhoon_pages||[],from_cache:!!m.from_cache}),m.invoice_count&&m.invoice_count>1&&showToast(t("multi-invoice-toast",{file:m.filename,n:m.invoice_count}),"success"),m.missed_invoice_warnings&&m.missed_invoice_warnings.length){const B=m.missed_invoice_warnings.map(function(P){return P.page}).filter(function(P){return P!=null});showToast(t("missed-invoice-warn",{file:m.filename,pages:B.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",m.missed_invoice_warnings)}if(m.typhoon_enhanced&&m.typhoon_pages&&m.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:m.filename,n:m.typhoon_pages.length}),"success"),m.fallback_used){const B=m.engine_chain||[],P=m.engine||"";let H;P==="typhoon_nvidia"?H="fallback-typhoon-nvidia-toast":P==="easyocr"?H="fallback-easyocr-toast":H="fallback-generic-toast",showToast(t(H,{file:m.filename}),"warn"),console.info("[OCR Chain]",B)}if(m.from_cache&&showToast(t("cache-hit-toast",{file:m.filename}),"info"),m.duplicate_warnings&&m.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const B of m.duplicate_warnings)window._dupQueue.push({filename:m.filename,...B})}return m.auto_pushed&&showToast(t("auto-push-fired",{file:m.filename}),"info"),m.quota&&m.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=m.quota.used_this_month,_userInfo.tenant_used=m.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(C){clearTimeout(b);try{window._ocrCtrls&&window._ocrCtrls.delete(v)}catch{}console.error("[Upload] failed for",c.file.name,C);const E=C&&(C.name==="AbortError"||C==="timeout"),m=E&&(v.signal.reason==="timeout"||C==="timeout"),h=C&&C.message&&/NetworkError|Failed to fetch/i.test(C.message);return E&&(v.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(m?c.errorKey="err.timeout":E?c.errorKey="err.aborted":h?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:C&&C.message?C.message:String(C)}),c.status="error",!u&&!window._ocrAborted&&(h||m)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise(B=>setTimeout(B,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?o(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=o;let s=0,i=!1;async function r(){for(;s<n.length&&!i&&!window._ocrAborted;){const c=s++,u=await o(n[c]);if(u&&u.abort){i=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const p=document.getElementById("btn-start"),l=document.getElementById("btn-stop");p&&(p.style.display="none"),l&&(l.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(n)}catch{}const d=[];for(let c=0;c<Math.min(a,n.length);c++)d.push(r());await Promise.all(d);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}p&&(p.style.display=""),l&&(l.style.display="none");const f=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const v of n)if(v.status==="success")c.success++;else if(v.status==="cancelled")c.cancelled++;else if(v.status==="error"){const b=v.errorKey||"";b==="err.network"?c.network++:b==="err.timeout"||b==="err.aborted"?c.timeout++:b.indexOf("quota")>=0||b==="err.monthly_limit_exceeded"?c.quota++:b==="err.gemini_overloaded"||b==="err.server"?c.overloaded++:b==="err.rate_limit"?c.rate++:c.other++}const u=n.length;f?showToast(Ma(c,u),"warn",4e3):u>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast($a(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function Ma(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function $a(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});async function nn(e){let n;if(e)n=_selectedFiles.find(a=>a.file===e)||{file:e,name:e.name,status:"waiting"};else{const a=_selectedFiles.filter(o=>o.status==="waiting");if(!a.length)return;n=a[0]}window._dmsLastFile=n.file,n.status="processing",typeof renderFileList=="function"&&renderFileList();try{const a=new FormData;a.append("file",n.file,n.name),a.append("push","true");const o=await fetch("/api/dms/id-card-booking",{method:"POST",headers:{Authorization:"Bearer "+token},body:a});if(o.status===401||o.status===403){const i=await o.clone().json().catch(()=>({})),r=i&&i.detail,p=typeof r=="string"?r:r&&r.code||"";if(!p||p.startsWith("auth.")){localStorage.removeItem("mrpilot_token"),showToast(t("alert-session"),"error"),setTimeout(()=>{window.location.href="/"},1200);return}}const s=await o.json().catch(()=>({}));if(!o.ok){n.status="error";const i=s&&s.detail&&(s.detail.code||s.detail)||"unknown";n.errorKey="err."+i,n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:String(i)}});return}n.status=s.ok||s.dms_push&&s.dms_push.status==="needs_review"?"success":"error",typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult(s),typeof updateStartButton=="function"&&updateStartButton()}catch{n.status="error",n.canRetry=!0,typeof renderFileList=="function"&&renderFileList(),typeof window.renderDmsIdCardResult=="function"&&window.renderDmsIdCardResult({ok:!1,dms_push:{status:"failed",error_code:"network"}})}}window._dmsRetryIdCard=function(){window._dmsLastFile&&nn(window._dmsLastFile)};function an(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=v=>v!=null?Number(v).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",p=v=>v||"—",l=v=>{try{const b=new Date(v);return`${b.getFullYear()}-${String(b.getMonth()+1).padStart(2,"0")}-${String(b.getDate()).padStart(2,"0")}`}catch{return v}},d=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",f=(e.matched_fields||[]).map(v=>{const b=t("dup-field-"+v.replace("_","-"))||v;return`<span class="dup-field-chip">${escapeHtml(b)}</span>`}).join(" "),c=document.createElement("div");c.className="log-detail-modal",c.innerHTML=`
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
    `,document.body.appendChild(c);const u=()=>{c.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(an,200)};c.querySelector(".dup-close").addEventListener("click",u),c.querySelector('[data-action="view"]').addEventListener("click",()=>{const v=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(v)},400),u()}),c.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const v=e.new_history_id;if(!v){u();return}try{(await fetch(`/api/history/${encodeURIComponent(v)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}u()}),c.querySelector('[data-action="keep"]').addEventListener("click",u)}window.showDuplicateDialog=an;function Ce(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function je(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Ha(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ce("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ce("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ce("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ce("time-day-ago-suffix"," 天前")}catch{return""}}async function Et(){on();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const p={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[l,d,f]=await Promise.all([fetch("/api/me/tenant-usage",{headers:p}).then(E=>E.ok?E.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:p}).then(E=>E.ok?E.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:p}).then(E=>E.ok?E.json():null).catch(()=>null)]),c=l&&l.ocr_this_month||0;let u=0;const v=d&&(d.items||d.history||d)||[],b=Array.isArray(v)?v:[];b.forEach(E=>{(E.status==="pending"||E.status==="reviewing")&&u++});const C=f&&(f.total||f.count||f.pending||0)||0;if(e&&(e.textContent=je(c)),n&&(n.textContent=je(u)),a&&(a.textContent=je(C)),r&&(C>0?(r.style.display="",r.textContent=C):r.style.display="none"),o&&l){const E=l.ocr_this_month||0,m=l.quota||0;o.textContent=je(E),s&&(s.textContent=m?E+" / "+je(m)+" 张":Ce("dash-kpi-plan-sub","本月用量"))}if(i)if(b.length===0)i.innerHTML='<div class="dash-recent-empty">'+Ce("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const E=b.slice(0,5).map(m=>{const h=(m.invoice_no||m.filename||m.id||"").toString(),M=(m.supplier_name||m.buyer_name||m.client_name||m.notes||"").toString(),B=Ha(m.created_at||m.upload_time||m.date),P=H=>String(H).replace(/[&<>"']/g,_=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[_]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+P(h)+'">'+P(h)+'</span><span class="dash-recent-mid" title="'+P(M)+'">'+P(M)+'</span><span class="dash-recent-time">'+P(B)+"</span></div>"}).join("");i.innerHTML=E}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Ce("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Et;async function on(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},p=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!p.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const l=await p.json(),d=!!l.is_owner,f=!!l.is_billing_exempt;if(!d)e.style.display="none";else if(e.style.display="",f)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const u=typeof l.balance_thb=="number"?l.balance_thb:0;if(a&&(a.textContent="฿"+u.toFixed(2),a.className=u<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const v=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",b=u<50?"#dc2626":"#6b7280",C=E=>typeof window.escapeHtml=="function"?window.escapeHtml(E):String(E).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[m]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+b+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+C(v)+"</a>"}}const c=typeof l.pages_this_month=="number"?l.pages_this_month:typeof l.my_invoice_count=="number"?l.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(c)),i){const u=c>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",v=typeof window.t=="function"?window.t(u,{used:c}):c+" pages";i.textContent=v}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=on;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Et,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Et()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function It(){return localStorage.getItem("mrpilot_token")||""}function ve(e){return document.getElementById(e)}var Ge=null,De=null;function sn(){De||(De=setInterval(function(){if(!document.hidden){var e=It();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Ge!==null&&a>Ge&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Ge=a}}).catch(function(){}))}},3e4))}function Aa(){De&&(clearInterval(De),De=null),Ge=null}window._startCreditsPoll=sn;window._stopCreditsPoll=Aa;sn();var Bt=null,Lt=0;function ja(){if(!ve("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),Pa()}}function rn(){var e=function(n,a){var o=ve(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Re(e){[1,2,3].forEach(function(s){var i=ve("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=ve("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=ve("tv2-back"),a=ve("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=ve("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(Lt).toLocaleString()+"</strong>"))}}function ht(){for(var e=1;e<=3;e++){var n=ve("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function We(e){var n=ve(e);n&&(n.textContent="",n.style.display="none")}function qe(e,n){var a=ve(e);a&&(a.textContent=n,a.style.display="")}function Ht(e){var n=ve("tv2-dt");n&&(n.textContent=e.name);var a=ve("tv2-drop");a&&a.classList.add("has-file"),We("tv2-se")}function Pa(){var e=ve("topup-v2-ov");ve("tv2-close").addEventListener("click",Pe),e.addEventListener("click",function(i){i.target===e&&Pe()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&Pe()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(l){l.classList.remove("active")}),r.classList.add("active");var p=ve("tv2-amt");p&&(p.value=r.dataset.val,We("tv2-ae"))}});var n=ve("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),We("tv2-ae")});var a=ve("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=ve("tv2-drop"),s=ve("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&Ht(r)})),s&&s.addEventListener("change",function(){s.files[0]&&Ht(s.files[0])}),ve("tv2-back").addEventListener("click",function(){var i=ht();if(i<=1){Pe();return}Re(i-1)}),ve("tv2-next").addEventListener("click",function(){var i=ht();i===1?Da():i===2?Re(3):qa()})}async function Da(){var e=ve("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){qe("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){qe("tv2-ae",he("topup-amount-too-large"));return}Lt=n;var a=ve("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+It()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=he("topup-submit-fail");try{var r=JSON.parse(s),p=r.detail;if(Array.isArray(p)&&p.length){var l=p[0]&&p[0].type||"";l.indexOf("less_than")>=0?i=he("topup-amount-too-large"):(l.indexOf("greater_than")>=0||l.indexOf("parsing")>=0)&&(i=he("topup-amount-invalid"))}else typeof p=="string"&&(i=p)}catch{}throw new Error(i)}var d=await o.json();Bt=d.request_id,Re(2)}catch(f){qe("tv2-ae",f.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function qa(){var e=ve("tv2-file");if(!e||!e.files||!e.files[0]){qe("tv2-se",he("topup-slip-required"));return}var n=ve("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=ve("tv2-payer"),s=ve("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+Bt,{method:"POST",headers:{Authorization:"Bearer "+It()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),Pe()}catch(p){qe("tv2-ue",he("topup-upload-fail")+" · "+p.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function Pe(){var e=ve("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){ja(),Bt=null,Lt=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=ve(a);o&&(o.value="")});var e=ve("tv2-file");e&&(e.value="");var n=ve("tv2-drop");n&&n.classList.remove("has-file","drag-over"),ve("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){We(a)}),rn(),Re(1),ve("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=ve("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(rn(),Re(ht()))});(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function p(V,W,te){let re=typeof t=="function"?t(V):null;return(!re||re===V)&&(re=W),te&&Object.keys(te).forEach(function(A){re=String(re).replace("{"+A+"}",String(te[A]))}),re}function l(){try{const V=localStorage.getItem(n);o=V?JSON.parse(V):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function d(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function f(V){const W=new Date(V),te=function(re){return re<10?"0"+re:""+re};return te(W.getHours())+":"+te(W.getMinutes())+":"+te(W.getSeconds())}function c(V){return String(V??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function u(V,W){try{typeof showToast=="function"?showToast(V,W||"info"):alert(V)}catch{}}function v(V){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(V).then(function(){u(p("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){b(V)}):b(V)}catch{b(V)}}function b(V){try{const W=document.createElement("textarea");W.value=V,W.style.position="fixed",W.style.opacity="0",document.body.appendChild(W),W.select();const te=document.execCommand("copy");document.body.removeChild(W),u(te?p("tc-toast-copied","已复制"):p("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{u(p("tc-toast-copy-fail","复制失败"),"error")}}function C(){const V=document.getElementById("tc-account-chip"),W=document.getElementById("tc-progress-chip");if(V&&(V.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),W){const te=a.length,re=a.filter(function(A){return o[A.id]}).length;W.textContent=re+" / "+te}}function E(){const V=document.getElementById("tc-checklist-body");if(!V)return;const W={};a.forEach(function(re){W[re.group]||(W[re.group]=[]),W[re.group].push(re)});const te=[];Object.keys(W).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+c(re)+"</div>"),W[re].forEach(function(A){const I=o[A.id]||"",w=I?"is-"+I:"";te.push('<div class="tc-check-item '+w+'" data-id="'+c(A.id)+'"><div class="tc-check-id">'+c(A.id)+'</div><div class="tc-check-desc">'+c(A.desc)+'</div><div class="tc-check-actions">'+m(A.id,"pass",I)+m(A.id,"fail",I)+m(A.id,"skip",I)+"</div></div>")}),te.push("</div>")}),V.innerHTML=te.join("")}function m(V,W,te){const re=te===W,A={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},I={pass:p("tc-status-pass","通过"),fail:p("tc-status-fail","失败"),skip:p("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+W:"")+'" data-id="'+c(V)+'" data-kind="'+W+'" title="'+c(I[W])+'">'+A[W]+"</button>"}function h(V){return s==="all"?!0:s==="js_error"?V.type==="js_error"||V.type==="promise_error":s==="api"?V.type==="api_error"||V.type==="api_fail":s==="api_slow"?V.type==="api_slow":s==="console"?V.type==="console_error"||V.type==="console_warn":!0}function M(){const V=document.getElementById("tc-logs-body"),W=document.getElementById("tc-logs-count");if(!V)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(h);if(W&&(W.textContent=String(te.length)),re.length===0){V.innerHTML='<div class="tc-logs-empty">'+c(p("tc-logs-empty","暂无异常"))+"</div>";return}const A=re.slice(0,100).map(function(I){const w=typeof I.detail=="object"?JSON.stringify(I.detail,null,2):String(I.detail||"");return'<div class="tc-log-item t-'+c(I.type)+'" data-ts="'+I.ts+'"><span class="tc-log-time">'+f(I.ts)+'</span><span class="tc-log-type">'+c(I.type)+'</span><div class="tc-log-summary">'+c(I.summary)+'<div class="tc-log-detail">'+c(w)+"</div></div></div>"}).join("");V.innerHTML=A,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(I){I.classList.toggle("active",I.getAttribute("data-filter")===s)})}function B(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&M(),P()},200))}window._tcOnNewLog=B;function P(){const V=document.getElementById("nav-test-badge");if(!V)return;const W=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;W>0?(V.style.display="",V.textContent=W>99?"99+":String(W)):V.style.display="none"}function H(){C(),E(),M(),P()}function _(){const V=[],W=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";V.push("# Pearnly "+e+" 测试结果"),V.push("- 账号:"+te),V.push("- 时间:"+W.toISOString().replace("T"," ").slice(0,19));const re=a.length,A=a.filter(function(Z){return o[Z.id]==="pass"}).length,I=a.filter(function(Z){return o[Z.id]==="fail"}).length,w=a.filter(function(Z){return o[Z.id]==="skip"}).length,R=re-A-I-w;V.push("- 进度:"+(A+I+w)+" / "+re+" · ✅ "+A+" · ❌ "+I+" · ⏭ "+w+" · 未测 "+R),V.push(""),V.push("| ID | 描述 | 状态 |"),V.push("|---|---|---|"),a.forEach(function(Z){const le=o[Z.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";V.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const z=a.filter(function(Z){return o[Z.id]==="fail"});z.length>0&&(V.push(""),V.push("## ❌ 失败项"),z.forEach(function(Z){V.push("- **"+Z.id+"** · "+Z.desc)}));const K=(window._pearnlyTcLogs||[]).slice(-30).reverse();return K.length>0&&(V.push(""),V.push("## 🔴 异常日志(最近 "+K.length+" 条)"),K.forEach(function(Z){if(V.push("- `"+f(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&V.push("  - "+le.slice(0,600))}})),V.join(`
`)}function g(V){const W=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(W.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+W.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),W.forEach(function(A){if(te.push("## `"+f(A.ts)+"` · "+A.type),te.push("- "+A.summary),A.detail){te.push("```");try{te.push(JSON.stringify(A.detail,null,2).slice(0,2e3))}catch{te.push(String(A.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function k(){const V=Date.now();fetch("/api/health").then(function(W){const te=Date.now()-V;W.ok?u(p("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):u(p("tc-toast-health-fail","后端无响应")+" ("+W.status+")","error")}).catch(function(){u(p("tc-toast-health-fail","后端无响应"),"error")})}function S(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}H(),u(p("tc-toast-cleared","session 状态已清空"),"success")}function T(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(V){return V.json()}).then(function(V){window._clientsCache=V.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),u("客户缓存已刷新 · "+(V.clients||[]).length+" 个客户","success")}).catch(function(){u("刷新失败","error")})}catch{}}function q(){if(i||!document.getElementById("page-test-center"))return;i=!0;const W=document.getElementById("tc-checklist-body");W&&W.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const U=ie.getAttribute("data-id"),Q=ie.getAttribute("data-kind");!U||!Q||(o[U]===Q?delete o[U]:o[U]=Q,d(),E(),C())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){o={},d(),E(),C()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){v(_())});const A=document.getElementById("tc-btn-copy-logs");A&&A.addEventListener("click",function(){v(g())});const I=document.getElementById("tc-btn-clear-logs");I&&I.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,M(),P()});const w=document.getElementById("tc-logs-filter");w&&w.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(s=ie.getAttribute("data-filter")||"all",M())});const R=document.getElementById("tc-logs-body");R&&R.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const z=document.getElementById("tc-tool-health");z&&z.addEventListener("click",k);const K=document.getElementById("tc-tool-clear-session");K&&K.addEventListener("click",S);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",T)}function L(){}window._tcApplyVisibility=L;let D=0;const Y=setInterval(function(){D++,_userInfo&&clearInterval(Y),D>60&&clearInterval(Y)},500);window.loadTestCenterPage=function(){l(),q(),H()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){P(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&H()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(h,M){if(typeof window.t=="function"){const B=window.t(h);if(B&&B!==h)return B}return M}function o(){const h=window._userInfo||{},M=String(h.role||"").toLowerCase(),B=String(h.tenant_role||"").toLowerCase();return h.is_super_admin===!0||h.is_owner===!0||M==="owner"||M==="admin"||B==="owner"||B==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const h=localStorage.getItem(e);if(!h||h==="null"||h==="0"||h==="")return null;const M=parseInt(h,10);return isNaN(M)?null:M}function r(h){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:h,mode:s()}}))}catch{}}function p(h){const M=i();h==null||h===0?localStorage.removeItem(e):(localStorage.setItem(e,String(h)),localStorage.setItem(n,"client")),String(M)!==String(h)&&r(h)}function l(){const h=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),h!=null&&r(null)}async function d(){try{const h=window.apiGet;if(typeof h!="function")return[];const M=await h("/api/workspace/clients");return M&&(M.clients||M.items)||[]}catch{return[]}}async function f(h){if(s()==="client"&&i()!=null)return typeof h=="function"&&h(),!0;const M=a("ws-need-client","这个功能需要先选择工作空间"),B=a("ws-btn-pick","选择工作空间"),P=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm(M,{okText:B,cancelText:P})&&c(h):window.confirm(M+`

[`+B+" / "+P+"]")&&c(h),!1}async function c(h){const M=await d();if(typeof h=="function"&&s()!=="personal"&&M.length===1){p(Number(M[0].id)),h();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:M,canCreate:o(),active:i(),onPersonal:l,onPick:function(B){p(Number(B)),typeof h=="function"&&h()},emptyHint:M.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!M.length){const B=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(B,"info")}}function u(h){const M=h||document.getElementById("workspace-switcher-root");if(!M)return;const B=s(),P=i();let H,_;if(B==="client"&&P!=null){const S=(window._workspaceClientsCache||[]).find(T=>Number(T.id)===Number(P));H=b("building"),_=S?S.name:a("ws-current-label","当前工作空间")}else H=b("user"),_=a("ws-personal","个人事务");M.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+H+'<span class="ws-ctrl-label">'+v(_)+"</span></button>";const g=M.querySelector("#ws-ctrl-btn");g&&g.addEventListener("click",()=>c(null))}function v(h){return String(h??"").replace(/[&<>"']/g,function(M){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[M]})}function b(h){const M='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return h==="building"?M+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':M+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function C(h){h=h||{};const M=h.clients||[],B=h.active,P=document.getElementById("ws-modal");P&&P.remove();const H=document.createElement("div");H.id="ws-modal",H.className="ws-modal";const g='<button type="button" class="ws-modal-item'+(s()==="personal"||B==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+b("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+v(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+v(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let k="";if(M.length){const D=['<option value="">'+v(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat(M.map(function(Y){const V=B!=null&&Number(B)===Number(Y.id);return'<option value="'+v(Y.id)+'"'+(V?" selected":"")+">"+v(Y.name||"#"+Y.id)+"</option>"}));k='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+v(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+D.join("")+"</select></div>"}const S=!M.length&&h.emptyHint?'<div class="ws-modal-empty">'+v(h.emptyHint)+"</div>":"",T=h.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+v(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+v(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+v(a("ws-create-submit","创建"))+"</button></div></div>":"";H.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+v(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+v(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+g+k+"</div>"+S+T+"</div>",document.body.appendChild(H);const q=H.querySelector("[data-ws-select]");q&&q.addEventListener("change",function(){const D=q.value;D&&(typeof h.onPick=="function"&&h.onPick(D),L(),u())});function L(){H.remove()}H.addEventListener("click",function(D){if(D.target===H||D.target.closest("[data-ws-close]")){L();return}if(D.target.closest("[data-ws-personal]")){typeof h.onPersonal=="function"&&h.onPersonal(),L(),u();return}const V=D.target.closest("[data-ws-pick]");if(V){const re=V.getAttribute("data-ws-pick");typeof h.onPick=="function"&&h.onPick(re),L(),u();return}if(D.target.closest("[data-ws-create-toggle]")){const re=H.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const A=re.querySelector("[data-ws-create-name]");A&&A.focus()}return}if(D.target.closest("[data-ws-create-submit]")){E(H,h,L);return}})}async function E(h,M,B){const P=h.querySelector("[data-ws-create-name]"),H=P?(P.value||"").trim():"";if(!H){P&&P.focus();return}let _=null;try{if(typeof window.apiPost=="function"){const k=await window.apiPost("/api/workspace/clients",{name:H});_=k&&typeof k.json=="function"?await k.json().catch(()=>null):k}}catch{_=null}const g=_&&(_.id||_.client&&_.client.id);if(!g){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await d(),p(Number(g)),M.onPick,B(),u()}window.openWorkspaceChooserUI=C,window.addEventListener("pearnly:workspace-changed",function(){u()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=p,window.enterPersonalMode=l,window.requireWorkspace=f,window.openWorkspaceChooser=c,window.renderWorkspaceControl=u,window.fetchWorkspaceClients=d;function m(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){c(null)},800)}catch{}}d().then(h=>{window._workspaceClientsCache=h,u(),m()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",u)})();(function(){const e=B=>document.querySelector('[data-num-target="'+B+'"]');function n(B){if(!B)return t("reconcile-last-activity-none");try{const P=new Date(B),H=new Date,_=H-P;if(_/6e4<5)return t("reconcile-last-activity-just-now");if(P.toDateString()===H.toDateString())return t("reconcile-last-activity-today");const k=Math.max(1,Math.floor(_/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",k)}catch{return t("reconcile-last-activity-none")}}function a(B,P,H){const _=e(B);_&&(_.textContent=H?"-":String(P),_.classList.toggle("is-empty",!!H))}function o(B){const P=document.getElementById("reconcile-error");P&&(P.style.display=B?"flex":"none")}function s(B){const P=document.getElementById("reconcile-empty");P&&(P.style.display=B?"flex":"none")}function i(B,P){const H=document.getElementById("reconcile-last-activity");H&&(H.textContent=B,H.classList.toggle("has-data",!!P))}function r(B){const P=!B||(B.total_sessions||0)===0;a("pending",B.pending||0,P),a("matched",B.matched||0,P),a("unmatched",B.unmatched||0,P),i(n(B.last_activity_at),!!B.last_activity_at),o(!1),s(P)}function p(B){const P=B.toUpperCase();return P==="KBANK"?"bank-chip-kbank":P==="SCB"?"bank-chip-scb":P==="BBL"?"bank-chip-bbl":P==="KTB"?"bank-chip-ktb":P==="TTB"?"bank-chip-ttb":"bank-chip-other"}function l(B,P){const H=_=>_?String(_).slice(0,10):"?";return!B&&!P?"":H(B)+" ~ "+H(P)}function d(B){return B==null?"":String(B).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(B){const P=document.getElementById("reconcile-recent"),H=document.getElementById("reconcile-recent-list");if(!P||!H)return;const _=(B||[]).slice(0,20);if(_.length===0){P.style.display="none";return}P.style.display="",s(!1),H.innerHTML=_.map(g=>{const k=g.parse_status==="parse_failed",S=g.bank_code||"OTHER",T=g.account_last4?" ···"+d(g.account_last4):"",q=l(g.period_start,g.period_end),L=d(g.source_filename||""),D=Number(g.tx_count||0),Y=k?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",D)+"</span>";return'<div class="recon-card" data-session-id="'+d(g.id)+'" data-session-name="'+L+'"><span class="bank-chip '+p(S)+'">'+d(S)+'</span><div class="recon-card-main"><div class="recon-card-title">'+L+T+'</div><div class="recon-card-sub">'+d(q)+'</div></div><div class="recon-card-right">'+Y+'</div><button class="recon-card-trash" data-trash="'+d(g.id)+'" title="'+d(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),H.querySelectorAll(".recon-card").forEach(g=>{g.addEventListener("click",k=>{k.target.closest(".recon-card-trash")||(g.dataset.sessionId,c())})}),H.querySelectorAll(".recon-card-trash").forEach(g=>{g.addEventListener("click",k=>{k.stopPropagation();const S=g.dataset.trash,T=g.closest(".recon-card"),q=T&&T.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(S,q)})})}function c(B){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const P=document.querySelector('[data-recon-tab="bank"]');P&&P.click()},150)}function u(){o(!0),s(!1)}function v(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const B=document.querySelector('[data-recon-tab="bank"]');B&&B.click()},150)}async function b(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const B=document.getElementById("reconcile-recent");B&&(B.style.display="none");const P={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[H,_]=await Promise.all([fetch("/api/bank-recon/stats",{headers:P}),fetch("/api/bank-recon/sessions?limit=20",{headers:P})]);if(!H.ok)throw new Error("http "+H.status);const g=await H.json(),k=_.ok?await _.json():[];r(g||{}),f(k||[])}catch(H){console.warn("[reconcile] load failed",H),u()}}function C(B){if(!B||!B.length)return;const P="Bearer "+(localStorage.getItem("mrpilot_token")||"");let H=0;const _=B.length;Array.from(B).forEach(function(g){const k=new FormData;k.append("file",g,g.name);const S=new XMLHttpRequest;S.open("POST","/api/bank-recon/upload"),S.setRequestHeader("Authorization",P),S.onload=function(){H++;try{const T=JSON.parse(S.responseText);S.status===200&&T.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",T.tx_count),"success"):showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error")}H===_&&setTimeout(b,600)},S.onerror=function(){H++,showToast(g.name+" "+(t("upload-failed")||"上传失败"),"error"),H===_&&setTimeout(b,600)},S.send(k)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function E(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const B=document.getElementById("reconcile-bank-file-input");B&&B.addEventListener("change",function(){C(this.files),this.value=""}),document.addEventListener("click",P=>{if(P.target.closest("#btn-reconcile-upload-top")||P.target.closest("#btn-reconcile-upload-empty")){v();return}if(P.target.closest("#btn-reconcile-retry")){b();return}if(P.target.closest("#btn-reconcile-dev-seed")){M();return}})}const m=["468b50c1-5593-4fd6-990d-515ce8085563"];function h(){const B=document.getElementById("btn-reconcile-dev-seed");if(!B)return;const P=typeof _userInfo<"u"?_userInfo:null,H=P&&P.id&&m.indexOf(String(P.id))>=0;B.style.display=H?"":"none"}async function M(){try{const B=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!B.ok)throw new Error("seed:"+B.status);const P=await B.json(),H=(t("reconcile-dev-seed-ok")||"").replace("{n}",P.tx_count||0);showToast(H,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const _=document.querySelector('[data-auto-tab="bank"]');_&&_.click(),P.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(P.session_id)},300)}catch(B){console.warn("[reconcile] dev seed failed",B),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){E(),h(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await b()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&b().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const b=a();if(b){if(!e.clients.length){b.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}b.innerHTML=e.clients.map(C=>{const E=String(C.id),m=e.selected.has(E)?"checked":"",h=escapeHtml(C.name||C.label||"#"+E),M=C.code?'<span class="assign-row-code">'+escapeHtml(C.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(E)+'" '+m+'><span class="assign-row-name">'+h+"</span>"+M+"</label>"}).join(""),p()}}function p(){const b=s();if(b){const E=t("assign-selected-count")||"已选 {n} / {total}";b.textContent=E.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const C=o();C&&(C.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function l(){const b=i();b&&(b.textContent=e.employeeName?" · "+e.employeeName:"")}async function d(b,C){e.employeeId=b,e.employeeName=C||"",e.opened=!0,e.selected=new Set,e.clients=[],l();const E=a();E&&(E.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const m=n();m&&(m.style.display="flex");try{const[h,M]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(b)+"/assignments")]);e.clients=h&&h.clients||[];const B=M&&M.client_ids||[];e.selected=new Set(B.map(String)),r()}catch(h){console.error("[assign-clients] load failed",h);const M=a();M&&(M.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function f(){e.opened=!1;const b=n();b&&(b.style.display="none")}async function c(){if(!e.employeeId)return;const b=Array.from(e.selected).map(E=>parseInt(E,10)).filter(E=>!isNaN(E)),C=document.getElementById("assign-modal-save");C&&(C.disabled=!0);try{const E=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:b});E&&E.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",b.length),"success"),f(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(E){console.error("[assign-clients] save failed",E),showToast(t("assign-save-failed")||"保存失败","error")}finally{C&&(C.disabled=!1)}}function u(){const b=n();if(!b||b.dataset.bound==="1")return;b.dataset.bound="1";const C=document.getElementById("assign-modal-close");C&&C.addEventListener("click",f);const E=document.getElementById("assign-modal-cancel");E&&E.addEventListener("click",f);const m=document.getElementById("assign-modal-save");m&&m.addEventListener("click",c),b.addEventListener("click",function(B){B.target===b&&f()});const h=o();h&&h.addEventListener("change",function(){h.checked?e.selected=new Set(e.clients.map(B=>String(B.id))):e.selected=new Set,r()});const M=a();M&&M.addEventListener("change",function(B){const P=B.target.closest('input[type="checkbox"][data-cid]');if(!P)return;const H=P.dataset.cid;P.checked?e.selected.add(H):e.selected.delete(H),p()})}function v(){e.opened&&(l(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",v),window.openAssignClientsModal=function(b,C){u(),d(b,C)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(f){if(!f)return"";try{return new Date(f).toLocaleString()}catch{return f}}function a(f){const c=document.getElementById("access-log-table");c&&(c.innerHTML='<div class="access-log-empty">'+escapeHtml(f)+"</div>");const u=document.getElementById("access-log-pager");u&&(u.innerHTML="")}function o(){const f=document.getElementById("access-log-table");if(!f)return;const c=e.rows||[];if(!c.length){a(t("set-access-log-empty"));return}const u=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,v=c.map(function(b){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(b.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(b.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(b.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(b.target_name||b.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(b.ip||"-")}</div>
                </div>`}).join("");f.innerHTML=u+v}function s(){const f=document.getElementById("access-log-pager");if(!f)return;const c=e.total||0;if(!c){f.innerHTML="";return}const u=e.page||1,v=e.per_page,b=Math.max(1,Math.ceil(c/v)),C=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",c),E=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",u).replace("{t}",b);f.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(C)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u-1}" ${u<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(E)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${u+1}" ${u>=b?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(f){const c=localStorage.getItem("mrpilot_token");if(c){e.page=f||1,a(t("set-access-log-loading"));try{const u="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),v=await fetch(u,{headers:{Authorization:"Bearer "+c}});if(v.status===403){a(t("set-access-log-empty"));return}if(!v.ok)throw new Error("http_"+v.status);const b=await v.json();e.rows=b.logs||[],e.total=b.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const f=localStorage.getItem("mrpilot_token");if(f)try{const c="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),u=await fetch(c,{headers:{Authorization:"Bearer "+f}});if(!u.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const v=await u.blob(),b=document.createElement("a"),C=URL.createObjectURL(v);b.href=C,b.download="pearnly_access_log.csv",document.body.appendChild(b),b.click(),setTimeout(function(){URL.revokeObjectURL(C),b.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function p(){const f=document.querySelectorAll(".set-tab-owner-only"),c=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));f.forEach(function(u){u.style.display=c?"":"none"})}document.addEventListener("click",function(f){if(f.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(f.target.closest("#access-log-csv-btn")){f.preventDefault(),r();return}const v=f.target.closest(".access-log-pager-btn[data-access-log-page]");if(v&&!v.disabled){const b=parseInt(v.dataset.accessLogPage,10);i(b)}}),document.addEventListener("input",function(f){f.target&&f.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(f.target.value||"").trim(),i(1)},350))});let l=0;const d=setInterval(function(){l++,_userInfo&&(p(),clearInterval(d)),l>60&&clearInterval(d)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){p(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=H=>document.getElementById(H);async function n(H,_){return await fetch(H,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(_||{})})}async function a(H){return await fetch(H,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(H,_){if(!H)return;H.style.display="",H.className="notif-line-check "+(_?"bound":"unbound");const g=_?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';H.innerHTML=g+"<span>"+escapeHtml(t(_?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(H){if(H==null)return"-";const _=Number(H);return isNaN(_)?String(H):"฿ "+_.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function p(H){if(!H)return"-";try{const _=new Date(H),g=(_.getMonth()+1).toString().padStart(2,"0"),k=_.getDate().toString().padStart(2,"0"),S=_.getHours().toString().padStart(2,"0"),T=_.getMinutes().toString().padStart(2,"0");return`${g}-${k} ${S}:${T}`}catch{return H}}function l(H){const _=e("notif-rules-list"),g=e("notif-rules-empty"),k=e("notif-rules-count");if(!(!_||!g)){if(k.textContent=String(H.length),k.className="auto-status-pill "+(H.length>0?"active":"none"),!H.length){g.style.display="",_.style.display="none",_.innerHTML="";return}g.style.display="none",_.style.display="",_.innerHTML=H.map(S=>{const T=S.template_code==="large_invoice",q=T?"notif-rule-large-tag":"notif-rule-exception-tag",L=T?"large":"";let D=[];if(T){const V=S.params&&S.params.threshold?r(S.params.threshold):"-";D.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+V)}S.enabled||D.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const Y=D.length?D.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${S.enabled?"":" disabled"}" data-rule-id="${S.id}">
                    <span class="notif-rule-tmpl-badge ${L}">${escapeHtml(t(q))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(S.name)}</div>
                        <div class="notif-rule-meta">${Y}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${S.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function d(H){const _=e("notif-logs-list");if(_){if(!H.length){_.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}_.innerHTML=H.map(g=>{const k=g.status==="sent",S=g.event_type==="exception_high"?"notif-event-exception-high":g.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",T=k?"":" · "+escapeHtml(g.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${k?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(S))}</div>
                        <div class="notif-log-meta">${escapeHtml(g.template_code||"-")}${T}</div>
                    </div>
                    <div class="notif-log-time">${p(g.sent_at)}</div>
                </div>`}).join("")}}async function f(){try{const H=await apiGet("/api/notifications/rules");c=H&&H.items||[],l(c)}catch(H){console.warn("load rules fail",H)}try{const H=await apiGet("/api/notifications/logs?limit=20");u=H&&H.items||[],d(u)}catch(H){console.warn("load logs fail",H)}}let c=null,u=null;function v(){c&&l(c),u&&d(u);const H=e("notif-new-modal");H&&H.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function b(){const H=e("notif-new-modal");H&&(H.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(_=>_.checked=!1),s().then(_=>i(e("notif-line-check"),!!(_&&_.bound))))}function C(){const H=e("notif-new-modal");H&&(H.style.display="none")}function E(){const H=document.querySelector('input[name="notif-template"]:checked'),_=e("notif-new-threshold-row");if(!H){_.style.display="none";return}_.style.display=H.value==="large_invoice"?"":"none";const g=e("notif-new-name");g&&!g.value.trim()&&(g.value=H.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function m(){const H=document.querySelector('input[name="notif-template"]:checked');if(!H){showToast(t("notif-new-template"),"error");return}const _=(e("notif-new-name").value||"").trim();if(!_){showToast(t("notif-name-required"),"error");return}const g={name:_,template_code:H.value,params:{},enabled:!0};if(H.value==="large_invoice"){const k=parseFloat(e("notif-new-threshold").value||"0");if(!k||k<=0){showToast(t("notif-threshold-required"),"error");return}g.params.threshold=k}try{const k=await apiPost("/api/notifications/rules",g);if(k&&k.ok)showToast(t("notif-toast-created"),"success"),C(),f();else{const S=await(k&&k.json&&k.json().catch(()=>({})))||{};showToast(S&&S.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function h(H,_,g){if(H==="toggle"){const k=g.classList.contains("on"),S=await n("/api/notifications/rules/"+_,{enabled:!k});S&&S.ok?(showToast(t(k?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),f()):showToast("toggle failed","error");return}if(H==="test"){const k=await s();if(!k||!k.bound){showToast(t("notif-line-error-bind-first"),"error");return}const S=await apiPost("/api/notifications/rules/"+_+"/test",{});if(S&&S.ok)showToast(t("notif-toast-test-sent"),"success"),f();else{const T=await(S&&S.json&&S.json().catch(()=>({})))||{},q=T&&T.detail||"";showToast(q||t("notif-toast-test-failed"),"error"),f()}return}if(H==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const S=await a("/api/notifications/rules/"+_);S&&S.ok?(showToast(t("notif-toast-deleted"),"success"),f()):showToast("delete failed","error");return}}let M=!1;function B(){if(M)return;M=!0;const H=e("notif-btn-new");H&&H.addEventListener("click",b);const _=e("notif-btn-refresh-logs");_&&_.addEventListener("click",f);const g=e("notif-new-close");g&&g.addEventListener("click",C);const k=e("notif-new-cancel");k&&k.addEventListener("click",C);const S=e("notif-new-save");S&&S.addEventListener("click",m),document.querySelectorAll('input[name="notif-template"]').forEach(L=>{L.addEventListener("change",E)});const T=e("notif-rules-list");T&&T.addEventListener("click",L=>{const D=L.target.closest("button[data-action]");if(!D)return;const Y=D.closest("[data-rule-id]");Y&&h(D.getAttribute("data-action"),Y.getAttribute("data-rule-id"),D)});const q=e("notif-new-modal");q&&q.addEventListener("click",L=>{L.target===q&&C()})}async function P(){B(),await f()}window._loadNotificationsPanel=P,window._rerenderNotifications=v})();(function(){function n(m,h){try{return window.t&&window.t(m)||h}catch{return h}}function a(){var m="";try{m=localStorage.getItem("mrpilot_token")||""}catch{}return m?{Authorization:"Bearer "+m}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var m=document.createElement("style");m.id="recon-batch-style",m.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(m)}}function i(m){return m?m.dataset&&m.dataset.taskId?m.dataset.taskId:m.dataset&&m.dataset.taskid?m.dataset.taskid:"":""}function r(m){var h=document.getElementById(m.tbody);if(!h)return null;var M=h.closest("table");if(!M)return null;var B=M.querySelector("thead");if(!B)return null;if(B._reconReady)return B;var P=B.querySelector("tr");if(!P)return null;if(P.classList.add("recon-thead-default"),!P.querySelector(".recon-master-cb")){var H=document.createElement("th");H.className="recon-sel-cell";var _=document.createElement("input");_.type="checkbox",_.className="recon-master-cb",_.setAttribute("aria-label","select all"),_.addEventListener("change",function(){f(m,_.checked)}),H.appendChild(_),P.insertBefore(H,P.firstElementChild)}var g=P.children[1];g&&!g.classList.contains("recon-time-col")&&g.classList.add("recon-time-col");var k=P.children.length,S=document.createElement("tr");S.className="recon-thead-batch";var T=document.createElement("th");T.className="recon-sel-cell";var q=document.createElement("input");q.type="checkbox",q.className="recon-master-cb",q.checked=!0,q.setAttribute("aria-label","select all"),q.addEventListener("change",function(){f(m,q.checked)}),T.appendChild(q);var L=document.createElement("th");return L.setAttribute("colspan",String(k-1)),L.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',S.appendChild(T),S.appendChild(L),B.appendChild(S),L.querySelector("[data-recon-del]").addEventListener("click",function(){b(m)}),L.querySelector("[data-recon-clear]").addEventListener("click",function(){v(m)}),B._reconReady=!0,u(m),B}function p(m){var h=document.getElementById(m.tbody);if(h){var M=h.querySelectorAll("tr");M.forEach(function(B){var P=i(B);if(P&&!B.querySelector(".recon-sel-cb")){var H=B.querySelector("td");if(H){var _=document.createElement("td");_.className="recon-sel-cell";var g=document.createElement("input");g.type="checkbox",g.className="recon-sel-cb",g.dataset.taskId=P,g.dataset.kind=m.kind,g.addEventListener("click",function(S){S.stopPropagation()}),g.addEventListener("change",function(){c(m)}),_.appendChild(g),B.insertBefore(_,H);var k=B.children[1];k&&!k.classList.contains("recon-time-col")&&k.classList.add("recon-time-col")}}}),c(m)}}function l(m){var h=document.getElementById(m.tbody);return h?Array.prototype.slice.call(h.querySelectorAll(".recon-sel-cb")):[]}function d(m){return l(m).filter(function(h){return h.checked}).map(function(h){return h.dataset.taskId})}function f(m,h){l(m).forEach(function(M){M.checked=!!h}),c(m)}function c(m){var h=d(m),M=l(m),B=document.getElementById(m.tbody);if(B){var P=B.closest("table"),H=P&&P.querySelector("thead");if(H){h.length>0?H.classList.add("recon-batch-mode"):H.classList.remove("recon-batch-mode"),H.querySelectorAll(".recon-master-cb").forEach(function(g){if(M.length===0){g.checked=!1,g.indeterminate=!1;return}h.length===M.length?(g.checked=!0,g.indeterminate=!1):h.length===0?(g.checked=!1,g.indeterminate=!1):(g.checked=!1,g.indeterminate=!0)});var _=H.querySelector("[data-recon-count]");_&&(_.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",h.length))}}}function u(m){var h=document.getElementById(m.tbody);if(h){var M=h.closest("table"),B=M&&M.querySelector("thead");if(B){var P=B.querySelector("[data-recon-del-label]"),H=B.querySelector("[data-recon-clear]");P&&(P.textContent=n("recon-batch-delete","批量删除")),H&&(H.textContent=n("recon-batch-clear","取消")),c(m)}}}function v(m){l(m).forEach(function(h){h.checked=!1}),c(m)}async function b(m){var h=d(m);if(h.length){var M=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",h.length),B=!1;try{typeof window.pearnlyConfirm=="function"?B=await window.pearnlyConfirm(M,n("recon-batch-delete-title","批量删除")):B=window.confirm(M)}catch{B=!1}if(B)try{var P=Object.assign({"Content-Type":"application/json"},a()),H=m.kind==="glv"?h.map(function(S){return parseInt(S,10)}):h,_=await fetch(m.api,{method:"POST",headers:P,body:JSON.stringify({ids:H})});if(!_.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var g=await _.json(),k=g&&(g.deleted!=null?g.deleted:g.count)||h.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",k),"success"),m.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function C(m){r(m),p(m);var h=document.getElementById(m.tbody);if(!(!h||h._reconBatchWatched)){h._reconBatchWatched=!0;var M=new MutationObserver(function(){p(m)});M.observe(h,{childList:!0,subtree:!1})}}function E(){s(),o.forEach(C),document.querySelectorAll(".recon-batch-bar").forEach(function(m){try{m.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",E):E(),setTimeout(E,1500),setTimeout(E,4e3),document.addEventListener("keydown",function(m){m.key==="Escape"&&o.forEach(function(h){d(h).length>0&&v(h)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(u)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(d){};function i(d){n=d;for(let u=1;u<=a;u++){const v=document.getElementById("ob-step-"+u);v&&(v.style.display=u===d?"block":"none")}document.querySelectorAll(".ob-dot").forEach(u=>{const v=parseInt(u.dataset.step,10);u.classList.toggle("active",v===d),u.classList.toggle("done",v<d)});const f=document.getElementById("ob-step-label");f&&(f.textContent=d+" / "+a);const c=document.getElementById("ob-next");if(c&&(c.textContent=d===a?t("ob-finish"):t("ob-next")),d===4){const u=document.getElementById("ob-line-input");u&&(u.value=e.line_id||"")}}function r(d){const f=document.querySelector(".onboarding-modal");if(!f)return;let c=f.querySelector(".ob-feedback");c||(c=document.createElement("div"),c.className="ob-feedback",f.appendChild(c)),c.textContent=d,c.classList.add("show"),setTimeout(()=>c.classList.remove("show"),1800)}document.addEventListener("click",d=>{const f=d.target.closest(".ob-option");if(!f)return;const c=f.parentElement;if(!c||!c.classList.contains("ob-options"))return;c.querySelectorAll(".ob-option").forEach(v=>v.classList.remove("selected")),f.classList.add("selected");const u=f.dataset.value;c.id==="ob-role-options"?e.role=u:c.id==="ob-volume-options"?e.monthly_volume=u:c.id==="ob-country-options"&&(e.country=u)}),document.addEventListener("click",d=>{d.target.id==="ob-skip"&&p()}),document.addEventListener("click",d=>{if(d.target.id==="ob-next"){if(n===4){const f=document.getElementById("ob-line-input");e.line_id=(f&&f.value||"").trim().replace(/^@+/,"")}p()}}),document.addEventListener("click",d=>{if(d.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const f=document.getElementById("onboarding-modal");f&&(f.style.display="none")}});function p(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):l()}async function l(){const d=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const f={};if(e.role&&(f.role=e.role),e.monthly_volume&&(f.monthly_volume=e.monthly_volume),e.country&&(f.country=e.country),e.line_id&&(f.line_id=e.line_id),Object.keys(f).length===0){d&&(d.style.display="none");return}try{const c=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(f)});c.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,f),setTimeout(()=>{d&&(d.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),console.warn("onboarding profile save failed",c.status),r(t("ob-fb-saved-local")),setTimeout(()=>{d&&(d.style.display="none")},1500))}catch(c){console.error("onboarding submit",c),localStorage.setItem("pilot_ob_pending",JSON.stringify(f)),d&&(d.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function p(){return"DHL Express (Thailand) Co., Ltd."}function l(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:p(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>d(),window.loadPrefsSettings=()=>f(),window.loadArchiveSettings=()=>u();function d(){const _=document.getElementById("settings-contact-grid");if(!_)return;const g=_contact?.phone||"086-889-2228",k=_contact?.line_id||"@Pearnly",S=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",T=_contact?.email||"hello@pearnly.com",q=_contact?.address||"Bangkok, Thailand";_.innerHTML=`
            <a class="contact-item" href="${escapeHtml(S)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(k)}</div>
                </div>
            </a>
            <a class="contact-item" href="mailto:${escapeHtml(T)}">
                <div class="contact-icon email">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-email"))}</div>
                    <div class="contact-value">${escapeHtml(T)}</div>
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
                    <div class="contact-value">${escapeHtml(q)}</div>
                </div>
            </div>
        `}async function f(){try{const _=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!_.ok)return;const g=await _.json(),k=document.getElementById("pref-dup-check");k&&(k.checked=!!g.enabled)}catch(_){console.warn("load prefs failed",_)}}const c=document.getElementById("pref-dup-check");c&&!c.dataset.bound&&(c.dataset.bound="1",c.addEventListener("change",async _=>{const g=_.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:g})})).ok?showToast(g?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(_.target.checked=!g,showToast(t("pref-save-failed"),"error"))}catch{_.target.checked=!g,showToast(t("pref-save-failed"),"error")}}));async function u(){const _=!!(_userInfo&&_userInfo.can_customize_archive);o=!_;const g=document.getElementById("archive-upgrade-banner");g&&(g.style.display=_?"none":"");const k=document.getElementById("archive-plus-badge");k&&(k.style.display=_?"none":"");try{const S=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!S.ok)throw new Error("load failed");const T=await S.json();e=Array.isArray(T.name_template)?T.name_template:[],n=T.folder_strategy||"by_month_seller"}catch(S){console.error("load archive settings failed",S),showToast(t("archive-load-failed"),"error");return}v(),b(),C(),E()}function v(){const _=document.getElementById("archive-rule-canvas");if(_){if(e.length===0){_.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}_.innerHTML=e.map((g,k)=>{const S=i[g.type]||{label:g.type},T=s[g.type]||"",q=g.type==="sep"?`"${escapeHtml(g.val||"_")}"`:escapeHtml(t(S.label));return`
                <span class="archive-token ${g.type}"
                      data-token-idx="${k}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${T}</span>
                    <span class="token-label">${q}</span>
                </span>
            `}).join("")}}function b(){const _=document.getElementById("archive-field-palette");if(!_)return;const g=["date","seller","category","amount","invoice","buyer","sep"];_.innerHTML=g.map(k=>{const S=i[k],T=s[k]||"";return`
                <button class="archive-palette-btn ${k}" data-add-field="${k}" ${o?"disabled":""}>
                    <span class="token-icon">${T}</span>
                    <span>${escapeHtml(t(S.label))}</span>
                </button>
            `}).join("")}function C(){document.querySelectorAll('input[name="folder-strategy"]').forEach(_=>{_.checked=_.value===n,_.disabled=o})}async function E(){const _=document.getElementById("archive-preview-name"),g=document.getElementById("archive-preview-hint");if(g&&(g.textContent=t("archive-preview-hint",{category:r()})),!!_){if(e.length===0){_.textContent="-";return}try{const S=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:l().merged_fields,name_template:e})})).json();_.textContent=(S.name||"-")+".pdf"}catch{_.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const _=document.getElementById("archive-rule-modal");!_||_.style.display==="none"||(v(),b(),E())};let m=-1;document.addEventListener("dragstart",_=>{const g=_.target.closest(".archive-token");!g||o||(m=parseInt(g.dataset.tokenIdx,10),g.classList.add("dragging"),_.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",_=>{document.querySelectorAll(".archive-token").forEach(g=>g.classList.remove("dragging","drop-target")),m=-1}),document.addEventListener("dragover",_=>{const g=_.target.closest(".archive-token");g&&(_.preventDefault(),_.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(k=>k.classList.remove("drop-target")),g.classList.add("drop-target"))}),document.addEventListener("drop",_=>{const g=_.target.closest(".archive-token");if(!g||m<0||o)return;_.preventDefault();const k=parseInt(g.dataset.tokenIdx,10);if(k===m)return;const S=e.splice(m,1)[0];e.splice(k,0,S),m=-1,v(),E()}),document.addEventListener("click",_=>{if(_.target.closest("#btn-open-archive-rule")||_.target.closest("#btn-open-archive-rule-from-settings")){const T=document.getElementById("archive-rule-modal");T&&(T.style.display="",u());return}if(_.target.closest("#archive-rule-modal-close")||_.target.id==="archive-rule-modal"){const T=document.getElementById("archive-rule-modal");T&&(T.style.display="none");return}const g=_.target.closest(".settings-nav-item");if(g){switchSettingsTab(g.dataset.settingsTab);return}if(o&&_.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const k=_.target.closest("[data-add-field]");if(k){const T=k.dataset.addField,q=i[T],L={type:T,...q.defaultCfg};e.push(L),v(),E();return}const S=_.target.closest(".archive-token");if(S&&!o){h(parseInt(S.dataset.tokenIdx,10));return}if(_.target.closest("#btn-archive-save"))return P();if(_.target.closest("#btn-archive-reset"))return H();(_.target.closest("#archive-token-close")||_.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),_.target.closest("#btn-archive-token-ok")&&M(),_.target.closest("#btn-archive-token-delete")&&B()}),document.addEventListener("change",_=>{_.target.name==="folder-strategy"&&(n=_.target.value)});function h(_){a=_;const g=e[_];if(!g)return;const k=document.getElementById("archive-token-body");let S="";g.type==="date"?S=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${g.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${g.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${g.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${g.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:g.type==="seller"?S=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${g.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:g.type==="amount"?S=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${g.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:g.type==="sep"?S=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${g.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${g.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${g.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(g.val)?"":escapeHtml(g.val||"")}">
                    </div>
                </div>`:S=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,k.innerHTML=S,document.getElementById("archive-token-modal").style.display="",k.querySelectorAll(".sep-chip").forEach(T=>{T.addEventListener("click",()=>{k.querySelectorAll(".sep-chip").forEach(L=>L.classList.remove("active")),T.classList.add("active");const q=document.getElementById("token-sep-custom");q&&(q.value="")})})}function M(){const _=e[a];if(_){if(_.type==="date")_.format=document.getElementById("token-date-format").value;else if(_.type==="seller")_.short=document.getElementById("token-seller-short").checked;else if(_.type==="amount")_.with_currency=document.getElementById("token-amount-currency").checked;else if(_.type==="sep"){const g=document.querySelector("#archive-token-body .sep-chip.active"),k=document.getElementById("token-sep-custom").value;_.val=k||(g?g.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",v(),E()}}function B(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",v(),E())}async function P(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const g=document.getElementById("archive-rule-modal");g&&(g.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function H(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",v(),C(),E())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,p=0,l=!1;function d(h){const M=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return h.preventDefault(),h.returnValue=M,M}function f(){l||(l=!0,window.addEventListener("beforeunload",d))}function c(){l&&(l=!1,window.removeEventListener("beforeunload",d))}function u(){if(document.getElementById("big-batch-progress"))return;const h=document.getElementById("file-list");if(!h||!h.parentNode)return;const M=document.createElement("div");M.id="big-batch-progress",M.className="big-batch-progress",M.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',h.parentNode.insertBefore(M,h);const B=document.getElementById("bbp-text");B&&(B.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function v(){const h=document.getElementById("big-batch-progress");h&&h.remove()}function b(){if(!i)return;let h=0;for(let S=0;S<i.length;S++){const T=i[S].status;(T==="success"||T==="error"||T==="cancelled")&&h++}const M=r,B=M>0?Math.min(100,Math.floor(100*h/M)):0,P=(Date.now()-p)/1e3;let H;if(h>=3&&P>1){const S=P/h;H=(M-h)*S}else H=(M-h)*6/6;const _=Math.max(1,Math.ceil(H/60)),g=document.getElementById("bbp-fill"),k=document.getElementById("bbp-text");g&&(g.style.width=B+"%"),k&&(h>=M?k.textContent=t("big-batch-progress-done").replace("{total}",M):k.textContent=t("big-batch-progress-running").replace("{done}",h).replace("{total}",M).replace("{min}",_))}function C(h){try{if(localStorage.getItem(o)==="1")return}catch{}const M=Math.max(1,Math.ceil(h*6/6/60)),B=t("big-batch-first-tip").replace("{n}",h).replace("{min}",M);typeof showToast=="function"&&showToast(B,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function E(h){!h||h.length<100||(i=h,r=h.length,p=Date.now(),u(),f(),C(r),s&&clearInterval(s),s=setInterval(b,250),b())}function m(){s&&(clearInterval(s),s=null),c(),i&&r>=100?(b(),setTimeout(v,1200)):v(),i=null,r=0}window._bigBatchStart=E,window._bigBatchStop=m,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&b()})})();(function(){let e=null,n=!1,a=!1;function o(g){return typeof escapeHtml=="function"?escapeHtml(g==null?"":String(g)):String(g??"")}function s(g,k){try{typeof showToast=="function"&&showToast(g,k||"info")}catch{}}function i(){const g=typeof _userInfo<"u"?_userInfo:null;return!!(g&&(g.role==="owner"||g.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function p(g){if(!g)return!1;const k=String(g.status||"").toLowerCase();return k==="exception"||k==="exception_pending"||k==="rejected"}async function l(g){if(n&&!g)return e;const k=localStorage.getItem("mrpilot_token");if(!k)return null;try{const S=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+k}});if(!S.ok)throw new Error("http_"+S.status);e=await S.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function d(){const g=document.getElementById("erp-connect-cards");if(!g)return;const k=e;let S,T=!1;k?k.configured?k.connected?(T=!0,S='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):S='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":S='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":S='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let q="";if(!k||!k.configured)q='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!k.connected)i()&&(q='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const I=!!k.auto_push,w=I?t("card-btn-disable"):t("card-btn-enable");q='<button type="button" class="'+(I?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(I?"1":"0")+'" title="'+o(I?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(w)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const L=k&&k.connected?"xero-card-desc-connected":"xero-card-desc-default",D=k&&k.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",Y=(function(){const I=t(L);return I===L?D:I})();let V='<div class="integration-row erp-connect-xero'+(T?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+S+'</div><div class="int-desc">'+o(Y)+'</div></div><div class="int-actions">'+q+"</div></div>";if(k&&k.configured&&k.connected&&i()){const I=k.organisations||[];let w="";if(I.length>0){w+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(I.length)))+"</div>",w+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",w+='<div class="erp-cc-orgs">',I.forEach(function(K){w+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(K.id)+'"'+(K.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(K.organisation_name||K.organisation_id)+"</span></label>"}),w+="</div>";const R=!!k.auto_push,z=R?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");w+='<div class="erp-cc-auto-push" title="'+o(z)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(R?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",w+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}V+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+w+"</div>"}const W=g.querySelector(".erp-connect-xero"),te=g.querySelector("#erp-xero-details");te&&te.remove(),W?W.outerHTML=V:g.insertAdjacentHTML("afterbegin",V);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(I){I.preventDefault();const w=document.getElementById("erp-xero-details");w&&(w.style.display=w.style.display==="none"?"":"none")});const A=document.getElementById("btn-xero-toggle-enabled");A&&A.addEventListener("click",async function(I){if(I.preventDefault(),A.disabled)return;const R=!(A.getAttribute("data-xero-enabled")==="1");if(!R)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}A.disabled=!0,await v(R,null)})}async function f(){const g=localStorage.getItem("mrpilot_token");if(g)try{const k=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+g}});if(!k.ok){let T="unknown";try{T=(await k.json()).detail||"unknown"}catch{}const q=String(T).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+q)||T),"error");return}const S=await k.json();S.redirect_url&&(window.location.href=S.redirect_url)}catch(k){s(t("xero-push-fail").replace("{err}",k.message||"network"),"error")}}async function c(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const k=localStorage.getItem("mrpilot_token");try{const S=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+k}});if(!S.ok)throw new Error("http_"+S.status);await l(!0),d()}catch(S){s(t("xero-push-fail").replace("{err}",S.message),"error")}}async function u(g){const k=localStorage.getItem("mrpilot_token");try{const S=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+k,"Content-Type":"application/json"},body:JSON.stringify({token_id:g})});if(!S.ok)throw new Error("http_"+S.status);await l(!0),d()}catch(S){s(t("xero-push-fail").replace("{err}",S.message),"error")}}async function v(g,k){const S=localStorage.getItem("mrpilot_token");k&&(k.disabled=!0);try{const T=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+S,"Content-Type":"application/json"},body:JSON.stringify({on:!!g})});if(!T.ok){let q="unknown";try{q=(await T.json()).detail||"unknown"}catch{}throw new Error(q)}s(g?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await l(!0),d()}catch(T){k&&(k.checked=!g),s(t("erp-auto-push-toggle-fail").replace("{err}",T.message||"network"),"error")}finally{k&&(k.disabled=!1)}}async function b(){const g=document.getElementById("drawer-history-save");if(!g||g.querySelector("#btn-xero-push")||g.querySelector("#pn-push-wrap")||(await l(!1),g.querySelector("#pn-push-wrap"))||g.querySelector("#btn-xero-push"))return;const k=r();if(!(k&&(k._historyId||k.history_id)))return;let T=!1,q="xero-push-tip";!e||!e.configured?(T=!0,q="xero-err-not_configured"):e.connected?p(k)&&(T=!0,q="xero-push-disabled-exc"):(T=!0,q="xero-push-disabled-no-conn");const L=document.createElement("button");L.type="button",L.id="btn-xero-push",L.className="btn btn-ghost"+(T?" disabled":""),L.disabled=T,L.title=t(q)||"",L.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",L.addEventListener("click",C);const D=document.getElementById("btn-push-erp");D&&D.parentNode?D.parentNode.insertBefore(L,D.nextSibling):g.insertBefore(L,g.firstChild)}async function C(){const g=r(),k=g&&(g._historyId||g.history_id);if(!k)return;const S=document.getElementById("btn-xero-push");S&&(S.disabled=!0,S.classList.add("loading"));const T=localStorage.getItem("mrpilot_token");try{const q=await fetch("/api/erp/xero/push/"+encodeURIComponent(k),{method:"POST",headers:{Authorization:"Bearer "+T}});if(!q.ok){let L="unknown";try{L=(await q.json()).detail||"unknown"}catch{}const D=String(L).replace(/^xero\./,"").toLowerCase(),Y=t("xero-"+D),V=Y&&Y!=="xero-"+D?Y:L;s(t("xero-push-fail").replace("{err}",V),"error");return}s(t("xero-push-ok"),"success")}catch(q){s(t("xero-push-fail").replace("{err}",q.message||"network"),"error")}finally{S&&(S.disabled=!1,S.classList.remove("loading"))}}async function E(){await l(!0),d(),m()}async function m(){const g=document.getElementById("erp-global-push-mode");if(!g)return;const k=localStorage.getItem("mrpilot_token");if(k)try{const S=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+k}});if(S.ok){const T=await S.json();T.mode&&(g.value=T.mode,g.dataset.prev=T.mode)}}catch{}}async function h(g){const k=g.value,S=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+S,"Content-Type":"application/json"},body:JSON.stringify({mode:k})})).ok?(g.dataset.prev=k,s(t("pref-erp-mode-saved"),"success")):(g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{g.value=g.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function M(){try{const g=String(window.location.hash||"");if(g.indexOf("xero=ok")>=0){const k=g.match(/n=(\d+)/),S=k?k[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",S),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),l(!0).then(d)}else g.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function B(){if(a)return;a=!0,document.addEventListener("click",function(k){if(k.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(E,50);return}if(k.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(E,80);return}if(k.target.closest("#btn-xero-connect")){k.preventDefault(),f();return}if(k.target.closest("#btn-xero-disconnect")){k.preventDefault(),c();return}}),document.addEventListener("change",function(k){k.target&&k.target.matches('input[name="xero-default-org"]')&&u(k.target.value),k.target&&k.target.id==="xero-auto-push-toggle"&&v(k.target.checked,k.target),k.target&&k.target.id==="erp-global-push-mode"&&h(k.target)});const g=function(){return document.getElementById("drawer-body")};try{const k=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&b()}),S=g();if(S)k.observe(S,{childList:!0,subtree:!0});else{const T=new MutationObserver(function(){const q=g();q&&(k.observe(q,{childList:!0,subtree:!0}),T.disconnect())});T.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout(M,500)}function P(){e&&d();const g=document.getElementById("btn-xero-push");if(g){const k=g.querySelector("span");k&&(k.textContent=t("xero-push-btn"))}}B(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",P);async function H(g){const k=Date.now();for(;Date.now()-k<g;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(S=>setTimeout(S,80))}return null}async function _(){await H(5e3);const g=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),k=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');g&&k&&await E()}setTimeout(_,200)})();(function(){var e="https://www.mrerp4sme.com/dms/index.php",n=null,a=!1;function o(E){return typeof escapeHtml=="function"?escapeHtml(E==null?"":String(E)):String(E??"")}function s(E,m){try{typeof showToast=="function"&&showToast(E,m||"info")}catch{}}function i(){return localStorage.getItem("mrpilot_token")}async function r(E){var m=i();if(!m)return null;try{var h=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+m}});if(!h.ok)throw new Error("http_"+h.status);var M=await h.json(),B=M&&M.items||[];n=B.find(function(P){return P&&(P.adapter||"").toLowerCase()==="mrerp_dms"})||null,a=!0}catch{n=null,a=!1}return n}function p(){var E=document.getElementById("erp-connect-cards");if(E){var m=E.querySelector("[data-mrerp-dms-zone]");m||(m=document.createElement("div"),m.setAttribute("data-mrerp-dms-zone","1"),E.appendChild(m));var h=n,M=!!(h&&h.enabled!==!1),B;h?M?B='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("dms-card-connected"))+"</span>":B='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-disabled-pill"))+"</span>":B='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("dms-card-not-connected"))+"</span>";var P;if(!h)P='<button type="button" class="int-btn-configure" id="btn-dms-connect">'+o(t("dms-card-connect"))+"</button>";else{var H=M?t("dms-card-disable"):t("dms-card-enable");P='<button type="button" class="int-btn-configure" id="btn-dms-edit">'+o(t("dms-card-edit"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-test">'+o(t("dms-card-test"))+'</button><button type="button" class="int-btn-configure" id="btn-dms-toggle">'+o(H)+"</button>"}m.innerHTML='<div class="integration-row erp-connect-mrerp-dms'+(M?" connected":"")+'"><div class="int-icon ic-mrerp-dms" style="background:#0a5c8a;color:#fff;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13l2-5a2 2 0 011.9-1.4h10.2A2 2 0 0119 8l2 5"/><path d="M3 13h18v4a1 1 0 01-1 1h-1a1 1 0 01-1-1v-1H6v1a1 1 0 01-1 1H4a1 1 0 01-1-1z"/><circle cx="7" cy="15.5" r="1"/><circle cx="17" cy="15.5" r="1"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("dms-card-title"))+"</span>"+B+'</div><div class="int-desc">'+o(t("dms-card-desc"))+'</div></div><div class="int-actions">'+P+"</div></div>"}}function l(){var E=document.getElementById("dms-wizard-overlay");E&&E.remove(),document.removeEventListener("keydown",d)}function d(E){E.key==="Escape"&&l()}function f(){l();var E=n,m=E&&E.config&&E.config.system_url||e,h=E&&E.config&&E.config.booking_defaults&&E.config.booking_defaults.booking_prefix||"PN",M=function(H,_,g,k,S){return'<label style="display:block;margin-bottom:12px;"><span style="display:block;font-size:13px;color:var(--muted,#6b6b66);margin-bottom:5px;">'+o(t(H))+'</span><input id="'+_+'" type="'+g+'" value="'+o(k||"")+'" placeholder="'+o(S||"")+'" autocomplete="new-password" style="width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--line,#ddd);border-radius:8px;font-size:14px;"></label>'},B=document.createElement("div");B.id="dms-wizard-overlay",B.style.cssText="position:fixed;inset:0;z-index:13000;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:16px;",B.innerHTML='<div class="dms-wizard mrerp-wizard" role="dialog" aria-modal="true" style="background:var(--card,#fff);border-radius:14px;max-width:440px;width:100%;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.18);max-height:90vh;overflow:auto;"><div style="font-size:17px;font-weight:700;margin-bottom:4px;">'+o(t("dms-wizard-title"))+'</div><div style="font-size:13px;color:var(--muted,#6b6b66);margin-bottom:18px;">'+o(t("dms-card-desc"))+"</div>"+M("dms-wizard-url","dms-w-url","text",m,e)+M("dms-wizard-username","dms-w-user","text","","")+M("dms-wizard-password","dms-w-pass","password","","")+M("dms-wizard-prefix","dms-w-prefix","text",h,"PN")+'<div id="dms-w-err" style="display:none;color:#b3261e;font-size:13px;margin:4px 0 12px;"></div><div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;"><button type="button" class="btn btn-ghost" id="dms-w-cancel">'+o(t("dms-wizard-cancel"))+'</button><button type="button" class="btn btn-primary" id="dms-w-save">'+o(t("dms-wizard-save"))+"</button></div></div>",document.body.appendChild(B),document.addEventListener("keydown",d),B.addEventListener("click",function(H){H.target===B&&l()});var P=document.getElementById("dms-w-user");P&&P.focus()}function c(E){var m=document.getElementById("dms-w-err");m&&(m.textContent=E,m.style.display=E?"":"none")}async function u(){var E=(document.getElementById("dms-w-url")||{}).value||"",m=(document.getElementById("dms-w-user")||{}).value||"",h=(document.getElementById("dms-w-pass")||{}).value||"",M=(document.getElementById("dms-w-prefix")||{}).value||"PN";if(E=E.trim(),m=m.trim(),!E||!m||!h){c(t("dms-wizard-required"));return}var B=document.getElementById("dms-w-save");B&&(B.disabled=!0,B.textContent=t("dms-wizard-saving")),c("");var P=i();try{var H=await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+P,"Content-Type":"application/json"},body:JSON.stringify({adapter:"mrerp_dms",config:{system_url:E,username:m,password:h}})}),_=await H.json().catch(function(){return{}});if(!H.ok||!_.ok){var g=_.error_friendly&&(_.error_friendly[window.currentLang]||_.error_friendly.en)||t("dms-connect-fail-generic");c(g),B&&(B.disabled=!1,B.textContent=t("dms-wizard-save"));return}var k={system_url:E,username_enc:m,password_enc:h,id_card_auto_push:!0,booking_defaults:{booking_prefix:M.trim()||"PN"}},S,T;n&&n.id?(S="PATCH",T="/api/erp/endpoints/"+encodeURIComponent(n.id)):(S="POST",T="/api/erp/endpoints");var q=S==="POST"?{name:"MR.ERP DMS",adapter:"mrerp_dms",config:k,is_default:!1,auto_push:!1}:{config:k,auto_push:!1},L=await fetch(T,{method:S,headers:{Authorization:"Bearer "+P,"Content-Type":"application/json"},body:JSON.stringify(q)});if(!L.ok){var D=await L.json().catch(function(){return{}}),Y=D&&D.detail&&(D.detail.code||D.detail)||"save_failed";c(t("dms-save-fail")+" ("+o(String(Y))+")"),B&&(B.disabled=!1,B.textContent=t("dms-wizard-save"));return}l(),s(t("dms-connect-ok"),"success"),await r(!0),p(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{c(t("dms-connect-fail-generic")),B&&(B.disabled=!1,B.textContent=t("dms-wizard-save"))}}async function v(){if(!(!n||!n.id)){s(t("dms-test-running"),"info");var E=i();try{var m=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id)+"/test-connection?refresh=1",{method:"POST",headers:{Authorization:"Bearer "+E}}),h=await m.json().catch(function(){return{}});s(h&&h.ok?t("dms-test-ok"):t("dms-test-fail"),h&&h.ok?"success":"error")}catch{s(t("dms-test-fail"),"error")}}}async function b(){if(!(!n||!n.id)){var E=n.enabled===!1;if(!E)try{var m=await window.pearnlyConfirm(t("dms-confirm-disable"));if(!m)return}catch{}var h=i();try{var M=await fetch("/api/erp/endpoints/"+encodeURIComponent(n.id),{method:"PATCH",headers:{Authorization:"Bearer "+h,"Content-Type":"application/json"},body:JSON.stringify({enabled:E})});if(!M.ok)throw new Error("http_"+M.status);s(E?t("dms-enabled-toast"):t("dms-disabled-toast"),"success"),await r(!0),p(),typeof window._refreshOcrDocMode=="function"&&window._refreshOcrDocMode()}catch{s(t("dms-save-fail"),"error")}}}function C(){r().then(p)}document.addEventListener("click",function(E){if(E.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(C,60);return}if(E.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(C,90);return}if(E.target.closest("#btn-dms-connect")||E.target.closest("#btn-dms-edit")){E.preventDefault(),f();return}if(E.target.closest("#dms-w-cancel")){E.preventDefault(),l();return}if(E.target.closest("#dms-w-save")){E.preventDefault(),u();return}if(E.target.closest("#btn-dms-test")){E.preventDefault(),v();return}if(E.target.closest("#btn-dms-toggle")){E.preventDefault(),b();return}}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("mrerp-dms-adapter",p),setTimeout(function(){var E=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),m=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');E&&m&&C()},250)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const d=`
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
        </div>`,f=document.createElement("div");f.innerHTML=d,document.body.appendChild(f.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",c=>{c.target.id==="report-modal"&&a()})}function a(){const d=document.getElementById("report-modal");d&&(d.style.display="none"),o=null}let o=null;async function s(d,f){const c=d+":"+(f||"");if(e[c])return e[c];let u;try{const v=localStorage.getItem("mrpilot_token"),b=await fetch(`/api/reports/templates?lang=${encodeURIComponent(d)}`,{headers:{Authorization:"Bearer "+v}});if(!b.ok)throw new Error("templates fetch failed");u=(await b.json()).templates||[]}catch(v){console.error("fetchTemplates fail",v),u=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(u=u.filter(v=>v.code!=="erp"),f==="history-batch"){const v=u.findIndex(C=>C.code==="standard"),b=v>=0?v+1:u.length;u.splice(b,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[c]=u,u}function i(d){const f=document.getElementById("report-tpl-list"),c=d.map((v,b)=>`
            <label class="report-tpl-item${v.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${v.code}" ${v.recommended||b===0?"checked":""}>
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
        `;f.innerHTML=c+u}function r(d){return d==null?"":String(d).replace(/[&<>"']/g,f=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[f])}function p(d){const f=new Date,c=f.getFullYear(),u=f.getMonth()+1;if(d==="all")return"all";if(d==="this-month")return`${c}-${String(u).padStart(2,"0")}`;if(d==="last-month"){const v=new Date(c,u-2,1);return`${v.getFullYear()}-${String(v.getMonth()+1).padStart(2,"0")}`}return d==="this-year"?`${c}`:d==="this-quarter"?`${c}-Q${Math.floor((u-1)/3)+1}`:"all"}window.openReportModal=async function(d){d=d||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(C=>{const E=C.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][E]&&(C.textContent=I18N[currentLang][E])});const f=document.getElementById("report-period-section");f&&(f.style.display=d.mode==="client"?"":"none");const c=document.getElementById("report-tpl-list");c.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const u=await s(currentLang,d&&d.mode);i(u),o=d;const v=document.getElementById("report-modal-download"),b=v.cloneNode(!0);v.parentNode.replaceChild(b,v),b.addEventListener("click",()=>l(o))};async function l(d){if(!d)return;const f=document.querySelector('input[name="report-tpl"]:checked');if(!f){showToast(t("report-toast-no-selection"),"info");return}const c=f.value,u=document.querySelector('input[name="report-period"]:checked'),v=u?u.value:"all",b=p(v),C=document.getElementById("report-modal-download"),E=C.innerHTML;C.disabled=!0,C.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const m=localStorage.getItem("mrpilot_token");let h,M;if(d.mode==="records")h=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+m,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,records:d.records||[],meta:d.meta||{}})}),M=`mrpilot-${c}-${Date.now()}.xlsx`;else if(d.mode==="client"){const S=`/api/reports/clients/${d.clientId}/export?template=${encodeURIComponent(c)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(b)}`;h=await fetch(S,{headers:{Authorization:"Bearer "+m}}),M=`${(d.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${c}.xlsx`}else if(d.mode==="history-batch")c==="sales_detail_th"?(h=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+m,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),M=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(h=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+m,"Content-Type":"application/json"},body:JSON.stringify({template:c,lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),M=`mrpilot-batch-${c}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+d.mode);if(!h.ok){let S="HTTP "+h.status;try{const T=await h.json();T&&T.detail&&(S=T.detail)}catch(T){console.warn("[batch-export] resp.json err.detail parse failed:",T)}h.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+S,"error");return}const B=await h.blob();let P=M;const _=(h.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(_)try{P=decodeURIComponent(_[1])}catch{}const g=URL.createObjectURL(B),k=document.createElement("a");k.href=g,k.download=P,document.body.appendChild(k),k.click(),document.body.removeChild(k),URL.revokeObjectURL(g),showToast(t("report-toast-success"),"success"),a()}catch(m){console.error("doDownload fail",m),showToast(t("report-toast-fail")+" · "+(m.message||""),"error")}finally{C.disabled=!1,C.innerHTML=E}}document.addEventListener("DOMContentLoaded",()=>{const d=document.getElementById("btn-export");if(d){const c=d.cloneNode(!0);d.parentNode.replaceChild(c,d),c.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(u=>({filename:u.filename,merged_fields:u.merged_fields||{}}))})})}const f=document.getElementById("history-batch-export");f&&f.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(d,f){openReportModal({mode:"client",clientId:d,clientName:f||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let i=null,r=null,p=null,l=60,d=!1,f=!1,c=0,u=0,v=0,b=[],C=null,E=!1;function m(){return i||(i=new Promise((x,$)=>{const j=indexedDB.open(o,s);j.onupgradeneeded=G=>{const N=G.target.result;N.objectStoreNames.contains("handles")||N.createObjectStore("handles"),N.objectStoreNames.contains("seen")||N.createObjectStore("seen"),N.objectStoreNames.contains("config")||N.createObjectStore("config")},j.onsuccess=G=>x(G.target.result),j.onerror=G=>$(G.target.error)}),i)}function h(x,$){return m().then(j=>new Promise((G,N)=>{const F=j.transaction(x,"readonly").objectStore(x).get($);F.onsuccess=()=>G(F.result),F.onerror=()=>N(F.error)}))}function M(x,$,j){return m().then(G=>new Promise((N,y)=>{const F=G.transaction(x,"readwrite");F.objectStore(x).put(j,$),F.oncomplete=()=>N(),F.onerror=()=>y(F.error)}))}function B(x,$){return m().then(j=>new Promise((G,N)=>{const y=j.transaction(x,"readwrite");y.objectStore(x).delete($),y.oncomplete=()=>G(),y.onerror=()=>N(y.error)}))}function P(x){return m().then($=>new Promise((j,G)=>{const N=$.transaction(x,"readwrite");N.objectStore(x).clear(),N.oncomplete=()=>j(),N.onerror=()=>G(N.error)}))}async function H(x){if(!x)return!1;try{const $={mode:"read"};let j=await x.queryPermission($);return j==="granted"?!0:(j=await x.requestPermission($),j==="granted")}catch($){return console.warn("[folder] permission check failed:",$),!1}}function _(x,$){const j=document.getElementById("folder-status-summary");j&&(j.setAttribute("data-i18n",x),j.textContent=t(x),j.className="auto-status-pill"+($?" "+$:""))}function g(x){["folder-unsupported","folder-empty","folder-active"].forEach($=>{const j=document.getElementById($);j&&(j.style.display=$===x?"":"none")})}function k(x){if(!x)return"-";const $=x instanceof Date?x:new Date(x),j=String($.getHours()).padStart(2,"0"),G=String($.getMinutes()).padStart(2,"0"),N=String($.getSeconds()).padStart(2,"0");return`${j}:${G}:${N}`}function S(){g("folder-active");const x=document.getElementById("folder-config-path");x&&r&&(x.textContent=r.name||"-");const $=document.getElementById("folder-interval-select");$&&($.value=String(l)),document.getElementById("folder-stat-last").textContent=C?k(C):"-",document.getElementById("folder-stat-processed").textContent=String(c),document.getElementById("folder-stat-failed").textContent=String(u),document.getElementById("folder-stat-queue").textContent=String(v);const j=document.getElementById("btn-folder-pause"),G=document.getElementById("btn-folder-resume");j&&(j.style.display=d?"none":""),G&&(G.style.display=d?"":"none"),d?_("folder-status-paused","paused"):_("folder-status-running","running");const N=document.getElementById("folder-status-text");N&&(N.setAttribute("data-i18n",d?"folder-status-paused":"folder-status-running"),N.textContent=t(d?"folder-status-paused":"folder-status-running"));const y=document.getElementById("folder-status-pulse");y&&(y.className="folder-status-pulse"+(d?" paused":"")),T()}function T(){const x=document.getElementById("folder-recent-list");if(x){if(b.length===0){x.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}x.innerHTML=b.slice(0,20).map($=>{let j;$.status==="ok"?j=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:$.status==="dup"?j=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:$.status==="skip"?j=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:j=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const G=$.status==="fail"&&$.error?$.error:$.status==="dup"&&$.reason||$.status==="skip"&&$.reason?$.reason:"",N=G?`<div class="folder-recent-err">${escapeHtml(G)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${j}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml($.name)}</div>
                        ${N}
                    </div>
                    <div class="folder-recent-time">${k($.time)}</div>
                </div>
            `}).join("")}}function q(x){b.unshift(x),b.length>50&&(b.length=50),M("config","recent_list",b).catch(()=>{})}async function L(x){const $=new FormData;$.append("file",x,x.name),$.append("source","folder");const j=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:$});if(!j.ok){let G="http_"+j.status;try{const N=await j.json();G=N&&N.detail?typeof N.detail=="string"?N.detail:N.detail.code||JSON.stringify(N.detail):G}catch{}throw new Error(G)}return await j.json()}async function D(x){try{const j=(await x.getFile()).size;return await new Promise(N=>setTimeout(N,3e3)),(await x.getFile()).size===j&&j>0}catch{return!1}}async function Y(x,$,j,G){if(G>10)return;let N;try{N=await x.queryPermission({mode:"read"})}catch{N="denied"}if(N==="granted")for await(const y of x.values()){const F=$?`${$}/${y.name}`:y.name;if(y.kind==="file"){if(!a.test(y.name))continue;let O;try{O=await y.getFile()}catch{continue}const J=`${F}::${O.size}::${O.lastModified}`;if(await h("seen",J))continue;j.push({entry:y,file:O,seenKey:J,relPath:F})}else if(y.kind==="directory")try{await Y(y,F,j,G+1)}catch{}}}async function V(){if(!(f||d||!r)){f=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),K(),showToast("warn",t("folder-permission-lost"));return}C=new Date;const $=[];await Y(r,"",$,0),v=$.length,S();for(const j of $){if(d)break;if(!await D(j.entry)){v=Math.max(0,v-1),S();continue}try{let N;try{N=await j.entry.getFile()}catch{N=j.file}const y=await L(N);await M("seen",j.seenKey,{name:N.name,relPath:j.relPath,size:N.size,lastModified:N.lastModified,processed_at:Date.now()});const F=y.history_ids||(y.history_id?[y.history_id]:[]),O=y.duplicate_warnings||[],J=j.relPath||N.name;F.length>0?(c+=F.length,q({name:J,status:"ok",time:new Date,history_id:F[0],count:F.length}),await M("config","processed_count",c)):O.length>0?q({name:J,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):q({name:J,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(N){u++,q({name:j.relPath||j.file.name,status:"fail",time:new Date,error:String(N.message||N)}),await M("config","failed_count",u)}v=Math.max(0,v-1),S()}}catch(x){console.warn("[folder] scan error:",x)}finally{f=!1,S()}}}function W(){p&&clearInterval(p),p=setInterval(V,l*1e3)}function te(){p&&(clearInterval(p),p=null)}function re(x){if(!r||d)return;const $=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return x.preventDefault(),x.returnValue=$,$}function A(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function I(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function w(){d=!1,W(),A(),S(),V()}function R(){d=!0,te(),I(),S()}function z(){d=!1,W(),A(),S(),V()}function K(){d=!0,te(),I()}async function Z(){try{const x=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await H(x)){showToast("warn",t("folder-permission-denied"));return}r=x,await M("handles","main",x),c=0,u=0,v=0,b=[],await M("config","processed_count",0),await M("config","failed_count",0),await P("seen"),w()}catch(x){x&&x.name!=="AbortError"&&console.warn("[folder] pick failed:",x)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(K(),r=null,c=0,u=0,v=0,b=[],await B("handles","main"),await B("config","processed_count"),await B("config","failed_count"),await P("seen"),g("folder-empty"),_("folder-status-empty",""))}async function ie(){b=[];try{await B("config","recent_list")}catch{}T()}async function U(){if(E)return;if(E=!0,!n){g("folder-unsupported"),_("folder-status-unsupported",""),ne();return}Q();let x=null;try{x=await h("handles","main")}catch{}if(!x){g("folder-empty"),_("folder-status-empty","");return}if(!await H(x)){g("folder-empty"),_("folder-status-empty",""),await B("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=x;try{c=await h("config","processed_count")||0}catch{}try{u=await h("config","failed_count")||0}catch{}try{const j=await h("config","recent_list");Array.isArray(j)&&(b=j.map(G=>({...G,time:G.time?new Date(G.time):new Date})))}catch{}w()}function Q(){const x=document.getElementById("btn-folder-pick"),$=document.getElementById("btn-folder-pause"),j=document.getElementById("btn-folder-resume"),G=document.getElementById("btn-folder-scan-now"),N=document.getElementById("btn-folder-remove"),y=document.getElementById("btn-folder-clear-recent"),F=document.getElementById("folder-interval-select");x&&x.addEventListener("click",Z),$&&$.addEventListener("click",R),j&&j.addEventListener("click",z),G&&G.addEventListener("click",()=>{V()}),N&&N.addEventListener("click",le),y&&y.addEventListener("click",ie),F&&F.addEventListener("change",O=>{l=parseInt(O.target.value,10)||60,d||W()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(x=>{x.dataset.tabJumpBound||(x.dataset.tabJumpBound="1",x.addEventListener("click",$=>{const j=$.currentTarget.dataset.tabJump;if(j==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(j==="upload"){const G=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');G&&G.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=U;function oe(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some($=>/chromium|google chrome|microsoft edge/i.test($.brand||""))}catch{}const x=navigator.userAgent||"";return!!(/Edg\//.test(x)||/Chrome\//.test(x)&&!/OPR\/|YaBrowser|Opera/.test(x))}function ue(){try{if(oe()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const x=document.getElementById("chrome-only-banner");if(!x)return;const $=x.querySelector('[data-i18n="chrome-banner-msg"]'),j=x.querySelector('[data-i18n="chrome-banner-dismiss"]');$&&typeof t=="function"&&($.textContent=t("chrome-banner-msg")),j&&typeof t=="function"&&(j.textContent=t("chrome-banner-dismiss")),x.style.display="";const G=document.getElementById("chrome-only-banner-close");G&&!G.dataset.bound&&(G.dataset.bound="1",G.addEventListener("click",()=>{x.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,n=null,a="new",o=!1,s=!1;async function i(){const L=document.getElementById("email-empty"),D=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!L||!D))try{const Y=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(Y.status===401){localStorage.removeItem("mrpilot_token");const W=await Y.json().catch(()=>({}));if((typeof W.detail=="string"?W.detail:W.detail&&W.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!Y.ok){p("none");return}const V=await Y.json();e=V.account||null,n=V.presets||{},o=!0,r(),e&&k()}catch(Y){console.error("[email-ingest] load failed",Y),p("none")}}function r(){const L=document.getElementById("email-empty"),D=document.getElementById("email-account-card"),Y=document.getElementById("email-logs-section");if(!e){L.style.display="",D.style.display="none",Y&&(Y.style.display="none"),p("none");return}L.style.display="none",D.style.display="",Y&&(Y.style.display="");const V=document.getElementById("email-account-addr"),W=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),A=document.getElementById("email-enabled-toggle");if(V&&(V.textContent=e.email_address||"-"),W&&(W.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const I=e.last_fetched_at;if(!I)te.textContent=t("email-last-never");else{const w=l(I),R=!e.last_error;te.textContent=R?t("email-last-ok",{time:w}):t("email-last-fail",{time:w})}}re&&(e.last_error?(re.style.display="",re.textContent=d(e.last_error)):re.style.display="none"),A&&(A.checked=!!e.enabled),e.enabled?e.last_error?p("error"):p("on"):p("off")}function p(L){const D=document.getElementById("email-status-summary");if(!D)return;D.classList.remove("none","ready","active","coming");let Y="auto-status-loading";L==="none"?(Y="email-status-none",D.classList.add("none")):L==="on"?(Y="email-status-on",D.classList.add("active")):L==="off"?(Y="email-status-off",D.classList.add("coming")):L==="error"&&(Y="email-status-error",D.classList.add("none")),D.setAttribute("data-i18n",Y),D.textContent=t(Y)}function l(L){if(!L)return"";const D=new Date(L);if(isNaN(D.getTime()))return"";const Y=V=>String(V).padStart(2,"0");return`${Y(D.getMonth()+1)}-${Y(D.getDate())} ${Y(D.getHours())}:${Y(D.getMinutes())}`}function d(L){if(!L)return"";const D=String(L);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(D)?t("email-test-auth-fail"):/timeout|timed out/i.test(D)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(D),D)}function f(L){a=L;const D=document.getElementById("email-modal");if(!D)return;const Y=document.getElementById("email-preset");Y.innerHTML="";const V=n||{},W=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};W.forEach(Q=>{if(!V[Q])return;const ee=document.createElement("option");ee.value=Q,ee.textContent=Q==="custom"?t("email-preset-custom"):te[Q]||Q,Y.appendChild(ee)});const re=document.getElementById("email-modal-title"),A=document.getElementById("email-address"),I=document.getElementById("email-password"),w=document.getElementById("email-imap-host"),R=document.getElementById("email-imap-port"),z=document.getElementById("email-imap-ssl"),K=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),U=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),L==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),A.value=e.email_address||"",I.value="",I.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),I.placeholder=t("email-field-password-edit-ph"),w.value=e.imap_host||"",R.value=e.imap_port||993,z.checked=e.imap_use_ssl!==!1,K.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),h(e.interval_min||15),Y.value=C(e.imap_host)||"custom",U&&(U.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),A.value="",I.value="",I.setAttribute("data-i18n-placeholder","email-field-password-ph"),I.placeholder=t("email-field-password-ph"),Y.value="gmail",u("gmail"),K.value="INBOX",Z.checked=!0,le.checked=!0;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=""),ee&&(ee.value=""),h(15),U&&(U.open=!1)}m(),D.style.display="flex",setTimeout(()=>A.focus(),60)}function c(){const L=document.getElementById("email-modal");L&&(L.style.display="none")}function u(L){const D=(n||{})[L];if(!D||L==="custom")return;const Y=document.getElementById("email-imap-host"),V=document.getElementById("email-imap-port"),W=document.getElementById("email-imap-ssl");Y&&(Y.value=D.host||""),V&&(V.value=D.port||993),W&&(W.checked=D.ssl!==!1)}const v={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function b(L){if(!L||!L.includes("@"))return;const D=L.split("@")[1].toLowerCase().trim(),Y=v[D];if(!Y)return;const V=document.getElementById("email-preset");if(!V)return;const W=V.value;W&&W!=="custom"&&W!==""&&W===Y||(V.value=Y,u(Y))}function C(L){if(!L)return null;const D=n||{};for(const Y in D)if(Y!=="custom"&&D[Y]&&D[Y].host===L)return Y;return null}function E(){const L=document.querySelector("#email-interval-options .email-interval-btn.active"),D=L?parseInt(L.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(D)?D:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function m(){const L=document.getElementById("email-interval-options");!L||L._bound||(L._bound=!0,L.addEventListener("click",D=>{const Y=D.target.closest(".email-interval-btn");Y&&(L.querySelectorAll(".email-interval-btn").forEach(V=>V.classList.remove("active")),Y.classList.add("active"))}))}function h(L){const D=[5,15,60].includes(L)?L:15,Y=document.getElementById("email-interval-options");Y&&Y.querySelectorAll(".email-interval-btn").forEach(V=>{V.classList.toggle("active",parseInt(V.dataset.interval,10)===D)})}function M(L,D){const Y=document.getElementById("email-test-result");Y&&(Y.style.display="",Y.textContent=D,Y.className="form-test-result "+(L==="ok"?"ok":L==="running"?"running":"fail"))}async function B(){const L=E();if(!L.email_address){M("fail",t("email-addr-required"));return}if(!L.password){M("fail",t("email-password-required"));return}if(!L.imap_host){M("fail",t("email-host-required"));return}const D=document.getElementById("btn-email-modal-test");D&&(D.disabled=!0),M("running",t("email-test-running"));try{const Y=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:L.email_address,password:L.password,imap_host:L.imap_host,imap_port:L.imap_port,imap_use_ssl:L.imap_use_ssl,folder:L.folder})}),V=await Y.json().catch(()=>({}));if(Y.ok&&V.success)M("ok",t("email-test-ok",{folder:L.folder,n:V.folder_count??"?"}));else{const W=V.error_msg||"";W==="auth_failed"||/auth/i.test(W)?M("fail",t("email-test-auth-fail")):M("fail",t("email-test-fail",{msg:W||Y.status}))}}catch(Y){M("fail",t("email-test-fail",{msg:String(Y).slice(0,120)}))}finally{D&&(D.disabled=!1)}}async function P(){const L=E();if(!L.email_address){M("fail",t("email-addr-required"));return}if(a==="new"&&!L.password){M("fail",t("email-password-required"));return}if(!L.imap_host){M("fail",t("email-host-required"));return}const D=document.getElementById("btn-email-modal-save");D&&(D.disabled=!0);const Y={...L};a==="edit"&&!Y.password&&delete Y.password;try{const V=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(Y)}),W=await V.json().catch(()=>({}));if(V.ok&&W.ok)e=W.account,showToast(t("email-save-ok"),"success"),c(),r(),k();else{const re="email."+(W.detail||"").split(".").slice(-1)[0];M("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{M("fail",t("email-save-fail"))}finally{D&&(D.disabled=!1)}}async function H(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const Y=document.getElementById("email-logs-list");Y&&(Y.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function _(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const L=document.getElementById("btn-email-trigger"),D=L?L.innerHTML:"";L&&(L.disabled=!0,L.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const Y=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),V=await Y.json().catch(()=>({}));if(Y.ok){const W=V.emails_scanned||0,te=V.ocr_succeeded||0,re=V.ocr_failed||0;W===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:W,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(V.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await i()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,L&&(L.disabled=!1,L.innerHTML=D)}}async function g(){if(!e)return;const L=document.getElementById("email-enabled-toggle"),D=!!(L&&L.checked),Y=e.enabled;try{const V=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:D})}),W=await V.json().catch(()=>({}));V.ok&&W.ok?(e=W.account,r()):(L&&(L.checked=Y),showToast(t("email-toggle-fail"),"error"))}catch{L&&(L.checked=Y),showToast(t("email-toggle-fail"),"error")}}async function k(){const L=document.getElementById("email-logs-list");if(L){L.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const D=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!D.ok){L.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const Y=await D.json();if(!Array.isArray(Y)||Y.length===0){L.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}L.innerHTML=Y.map(S).join("")}catch{L.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function S(L){const D=l(L.created_at),Y=L.status||"failed",V=Y==="success"?"ok":Y==="partial"?"partial":"fail",W=Y==="success"?"✓":Y==="partial"?"◐":"✗",te=L.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:L.emails_scanned||0,att:L.attachments_found||0,ok:L.ocr_succeeded||0,fail:L.ocr_failed||0}),A=(L.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${V}">
                <span class="log-time">${escapeHtml(D)}</span>
                <span class="log-status">${W}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(A)}</span>
            </div>
        `}function T(){const L=document.getElementById("btn-email-bind");L&&L.addEventListener("click",()=>f("new"));const D=document.getElementById("btn-email-edit");D&&D.addEventListener("click",()=>f("edit"));const Y=document.getElementById("btn-email-unbind");Y&&Y.addEventListener("click",H);const V=document.getElementById("btn-email-trigger");V&&V.addEventListener("click",_);const W=document.getElementById("email-enabled-toggle");W&&W.addEventListener("change",g);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",c);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",c);const A=document.getElementById("btn-email-modal-test");A&&A.addEventListener("click",B);const I=document.getElementById("btn-email-modal-save");I&&I.addEventListener("click",P);const w=document.getElementById("email-preset");w&&w.addEventListener("change",K=>u(K.target.value));const R=document.getElementById("email-address");R&&!R.dataset.autoBound&&(R.dataset.autoBound="1",R.addEventListener("blur",K=>b((K.target.value||"").trim())),R.addEventListener("input",K=>{const Z=(K.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&b(Z)}));const z=document.getElementById("btn-email-refresh-logs");z&&z.addEventListener("click",()=>{z.classList.add("spinning"),setTimeout(()=>z.classList.remove("spinning"),600),k()})}T(),window._loadEmailIngestPanel=i,window._rerenderEmailIngest=function(){if(!o)return;r();const L=document.getElementById("email-logs-section");e&&L&&L.open&&k()};let q=null;window._startEmailLogAutoRefresh=function(){q||(q=setInterval(()=>{e&&o&&k()},3e4))},window._stopEmailLogAutoRefresh=function(){q&&(clearInterval(q),q=null)}})();(function(){let e=[],n=null,a=[],o="all",s=null,i=!1;async function r(){if(i){T();return}i=!0,p(),await l(),T()}function p(){const y=document.getElementById("bank-file-input");y&&!y._bound&&(y._bound=!0,y.addEventListener("change",b));const F=document.getElementById("btn-bank-queue-clear-done");F&&!F._bound&&(F._bound=!0,F.addEventListener("click",B));const O=document.getElementById("btn-bank-back");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",()=>{n=null,a=[],te()}));const J=document.getElementById("btn-bank-delete");J&&!J._bound&&(J._bound=!0,J.addEventListener("click",g));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",_)),document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{o=fe.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(me=>{me.classList.toggle("active",me===fe)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const se=document.getElementById("btn-bank-cand-ignore");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",k));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",k));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",I)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",w))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",z)),document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{q=fe.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(me=>{me.classList.toggle("active",me===fe)}),L()}))})}async function l(){try{const y=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!y.ok)throw new Error("sessions:"+y.status);e=await y.json(),L()}catch(y){console.warn("[bank-recon] loadSessions failed",y),e=[],L()}}async function d(y){try{const F="/api/bank-recon/sessions/"+encodeURIComponent(y)+(o!=="all"?"?filter="+o:""),O=await fetch(F,{headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("detail:"+O.status);const J=await O.json();n=J.session,a=J.transactions||[],W()}catch(F){console.warn("[bank-recon] loadSessionDetail failed",F),showToast(t("bank-load-failed"),"error")}}let f=[],c=0;const u=3;function v(){return c+=1,"q"+c+"_"+Date.now()}async function b(y){const F=Array.from(y.target.files||[]);if(y.target.value="",F.length!==0){for(const O of F){const J={id:v(),file:O,name:O.name,size:O.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};O.name.toLowerCase().endsWith(".pdf")?O.size>20*1024*1024&&(J.status="failed",J.error_code="bank_recon.file_too_large"):(J.status="failed",J.error_code="bank_recon.only_pdf"),f.push(J)}C(),E(),P()}}function C(){const y=document.getElementById("bank-upload-queue");y&&(y.style.display=""),oe(),ue()}function E(){const y=document.getElementById("bank-upload-queue-list"),F=document.getElementById("bank-upload-queue-summary");if(!y)return;if(f.length===0){y.innerHTML="",F&&(F.textContent="");const se=document.getElementById("bank-upload-queue");se&&(se.style.display="none");return}let O=0,J=0,X=0,de=0;for(const se of f)se.status==="ok"?O++:se.status==="failed"?J++:se.status==="uploading"||se.status==="parsing"?X++:de++;F&&(F.textContent=t("bank-queue-summary").replace("{ok}",O).replace("{run}",X).replace("{wait}",de).replace("{fail}",J)),y.innerHTML=f.map(m).join(""),y.querySelectorAll("[data-q-act]").forEach(se=>{const ce=se.dataset.qAct,ae=se.dataset.qId;se.addEventListener("click",()=>{ce==="retry"&&h(ae),ce==="remove"&&M(ae)})})}function m(y){const F=(y.size/1024).toFixed(0)+" KB";let O="",J="";if(y.status==="pending")O='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",J='<button data-q-act="remove" data-q-id="'+N(y.id)+'" class="bq-act">×</button>';else if(y.status==="uploading")O='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(y.progress||0)+'%"></div></div>';else if(y.status==="parsing")O='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(y.status==="ok")O='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",y.tx_count||0)+"</span>",J='<button data-q-act="remove" data-q-id="'+N(y.id)+'" class="bq-act">×</button>';else if(y.status==="failed"){const X=x(y.error_code||"unknown");O='<span class="bq-stat bq-fail" title="'+N(X)+'">'+N(X)+"</span>",J='<button data-q-act="retry" data-q-id="'+N(y.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+N(y.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+N(y.id)+'"><div class="bq-name" title="'+N(y.name)+'">'+N(y.name)+'</div><div class="bq-size">'+F+'</div><div class="bq-status">'+O+'</div><div class="bq-actions">'+J+"</div></div>"}function h(y){const F=f.find(O=>O.id===y);F&&(F.status="pending",F.error_code=null,F.progress=0,E(),P())}function M(y){const F=f.findIndex(J=>J.id===y);if(F<0)return;const O=f[F];O.status==="uploading"||O.status==="parsing"||(f.splice(F,1),E())}function B(){f=f.filter(y=>y.status!=="ok"),E()}async function P(){for(;;){if(f.filter(O=>O.status==="uploading"||O.status==="parsing").length>=u)return;const F=f.find(O=>O.status==="pending");if(!F){f.every(O=>O.status==="ok"||O.status==="failed")&&(await l(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}H(F).then(()=>P())}}async function H(y){y.status="uploading",y.progress=0,E();try{const F=new FormData;F.append("file",y.file,y.name);const O=await new Promise((X,de)=>{const se=new XMLHttpRequest;se.open("POST","/api/bank-recon/upload"),se.setRequestHeader("Authorization","Bearer "+token),se.upload.onprogress=ce=>{ce.lengthComputable&&(y.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),E())},se.upload.onload=()=>{y.status="parsing",E()},se.onload=()=>{se.status>=200&&se.status<300?X({status:se.status,text:se.responseText}):X({status:se.status,text:se.responseText})},se.onerror=()=>de(new Error("network")),se.send(F)});let J={};try{J=JSON.parse(O.text||"{}")}catch{J={}}if(O.status>=400){y.status="failed",y.error_code=J&&J.detail||"unknown",E();return}if(J.parse_status==="parse_failed"){y.status="failed",y.error_code=J.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",E();return}y.status="ok",y.tx_count=J.tx_count||0,y.session_id=J.session_id||null,E()}catch(F){console.warn("[bank-recon] upload failed",F),y.status="failed",y.error_code="network",E()}}async function _(){if(!n)return;const y=document.getElementById("btn-bank-run-match"),F=y.innerHTML;y.disabled=!0,y.innerHTML="<span>"+t("bank-matching")+"</span>";try{const O=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("match:"+O.status);const J=await O.json();showToast(t("bank-match-done").replace("{matched}",J.matched).replace("{suggested}",J.suggested).replace("{unmatched}",J.unmatched),"success"),await d(n.id),await l()}catch(O){console.warn("[bank-recon] match failed",O),showToast(t("bank-match-failed"),"error")}finally{y.disabled=!1,y.innerHTML=F}}async function g(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const F=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!F.ok)throw new Error("delete:"+F.status);showToast(t("bank-deleted"),"success"),n=null,a=[],te(),await l()}catch(F){console.warn("[bank-recon] delete failed",F),showToast(t("bank-delete-failed"),"error")}}async function k(){if(s)try{const y=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!y.ok)throw new Error("ignore:"+y.status);ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function S(y){if(s)try{const F=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:y})});if(!F.ok)throw new Error("pick:"+F.status);showToast(t("bank-matched-ok"),"success"),ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function T(){const y=document.getElementById("bank-status-summary");if(!y)return;if(e.length===0){y.textContent=t("bank-pill-none");return}let O=0;for(const J of e)J.parse_status==="parsed"&&(J.unmatched_count||0)>0&&O++;y.textContent=O>0?t("bank-pill-pending").replace("{n}",O):t("bank-pill-ok")}let q="all";function L(){const y=document.getElementById("bank-sessions-list");if(!y)return;let F=e||[];if(q==="parsed"?F=F.filter(O=>O.parse_status==="parsed"):q==="failed"&&(F=F.filter(O=>O.parse_status==="parse_failed")),!e||e.length===0){y.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(F.length===0){y.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}y.innerHTML=F.map(O=>Y(O)).join(""),y.querySelectorAll(".bank-session-row").forEach(O=>{O.addEventListener("click",J=>{J.target.closest(".bank-session-trash")||d(O.dataset.sessionId)})}),y.querySelectorAll(".bank-session-trash").forEach(O=>{O.addEventListener("click",J=>{J.stopPropagation();const X=O.dataset.sessionId,de=O.dataset.sessionName||"";D(X,de)})})}async function D(y,F){if(!y)return;const O=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",F||"");if(await showConfirm(O,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(y),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===y&&(n=null,a=[],te()),await l(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=D;function Y(y){const F=(y.bank_code||"OTHER").toUpperCase(),O=G(y.period_start,y.period_end),J=y.account_last4?"···"+y.account_last4:"",X=V(y),de=j(y.created_at);return`
            <div class="bank-session-row" data-session-id="${N(y.id)}">
                <div class="bank-session-bank bk-${N(F)}">${N(F)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${N(y.source_filename||O||"-")}</div>
                    <div class="bank-session-meta">${N(O)} · ${N(J)} · ${N(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${N(y.id)}" data-session-name="${N(y.source_filename||"")}" title="${N(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function V(y){if(y.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(y.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const F=y.tx_count||0,O=y.matched_count||0,J=y.unmatched_count||0,X=[`<span class="bank-session-count">${F} ${t("bank-count-tx")}</span>`];return O>0&&X.push(`<span class="bank-session-count cnt-matched">${O} ${t("bank-count-matched")}</span>`),J>0&&X.push(`<span class="bank-session-count cnt-unmatched">${J} ${t("bank-count-unmatched")}</span>`),X.join("")}function W(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",K(),Z(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const y=document.getElementById("bank-detail-body");y&&y.classList.remove("has-pane"),s=null}function re(){const y=document.getElementById("bank-client-badge");if(!y||!n)return;const F=n.client_id,O=document.getElementById("bank-client-badge-dot"),J=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,se=!(de&&de.role==="member");if(F!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(F));y.classList.remove("is-empty"),O&&(O.style.background=ce&&ce.color||"#111111"),J&&(J.textContent=ce&&(ce.short_name||ce.name)||"#"+F)}else y.classList.add("is-empty"),O&&(O.style.background=""),J&&(J.textContent=t("bank-client-none"));se?(y.classList.remove("is-readonly"),y.disabled=!1,X&&(X.style.display="")):(y.classList.add("is-readonly"),y.disabled=!0,X&&(X.style.display="none")),y.style.display=""}let A=null;function I(){if(!n)return;const y=typeof _userInfo<"u"?_userInfo:null;if(!!(y&&y.role==="member"))return;A=n.client_id!=null?Number(n.client_id):null,R();const O=document.getElementById("bank-client-picker-modal");O&&(O.style.display="")}function w(){const y=document.getElementById("bank-client-picker-modal");y&&(y.style.display="none"),A=null}function R(){const y=document.getElementById("bank-client-picker-list");if(!y)return;const F=(window._clientsCache||[]).filter(J=>J&&(J.is_active===!0||J.is_active===void 0)),O=[];O.push('<div class="bank-client-picker-row is-none'+(A==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+N(t("bank-client-picker-none"))+"</span></div>"),F.forEach(J=>{const X=Number(J.id)===Number(A)?" is-selected":"";O.push('<div class="bank-client-picker-row'+X+'" data-cid="'+N(J.id)+'"><span class="bank-cp-dot" style="background:'+N(J.color||"#111111")+'"></span><span>'+N(J.short_name||J.name||"#"+J.id)+"</span></div>")}),y.innerHTML=O.join(""),y.querySelectorAll(".bank-client-picker-row").forEach(J=>{J.addEventListener("click",()=>{const X=J.dataset.cid;A=X?Number(X):null,R()})})}async function z(){if(n)try{const y=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:A})});if(!y.ok)throw new Error("client:"+y.status);n.client_id=A,re(),showToast(t("bank-client-changed"),"success"),w();try{await l()}catch{}}catch(y){console.warn("[bank-recon] save client failed",y),showToast(t("bank-client-change-failed"),"error")}}function K(){if(!n)return;const y=n;document.getElementById("bank-detail-title").textContent=(y.bank_code||"-")+(y.account_last4?" ···"+y.account_last4:"")+" · "+(y.source_filename||""),document.getElementById("bank-meta-period").textContent=G(y.period_start,y.period_end)||"-",document.getElementById("bank-meta-opening").textContent=$(y.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+$(y.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+$(y.total_outflow),document.getElementById("bank-meta-closing").textContent=$(y.closing_balance);const F=a||[],O=F.length;let J=0,X=0,de=0;for(const se of F){const ce=se.match_status||"unmatched";ce==="matched"?J++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=O,document.getElementById("bank-stat-matched").textContent=J,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const y=document.getElementById("bank-tx-tbody");if(!y)return;let F=a||[];if(o!=="all"&&(F=F.filter(O=>o==="matched"?O.match_status==="matched":o==="suggested"?O.match_status==="suggested":o==="unmatched"?O.match_status==="unmatched"||O.match_status==="ignored":!0)),F.length===0){y.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(y.innerHTML=F.map(O=>le(O)).join(""),y.querySelectorAll("tr[data-tx-id]").forEach(O=>{O.addEventListener("click",()=>{const J=O.dataset.txId,X=a.find(de=>de.id===J);X&&(y.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),O.classList.add("is-selected"),ie(X))})}),s){const O=y.querySelector('tr[data-tx-id="'+s.id+'"]');O&&O.classList.add("is-selected")}}function le(y){const F=y.direction==="OUT",O=F?"-":"+",J=F?"bank-out":"bank-in",X=y.match_status||"unmatched",de=t("bank-match-"+X)||X,se=j(y.tx_date),ce=y.channel?`<span class="bank-tx-channel">${N(y.channel)}</span>`:"";return`
            <tr data-tx-id="${N(y.id)}">
                <td class="bank-tx-date">${N(se)}</td>
                <td class="bank-tx-desc">${ce}${N(y.description||"-")}</td>
                <td class="bank-td-amount ${J}">${O}${$(y.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${N(de)}</span></td>
            </tr>
        `}async function ie(y){s=y;const F=document.getElementById("bank-detail-body");F&&F.classList.add("has-pane");const O=document.getElementById("bank-cand-pane-title"),J=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(O&&(O.textContent=t("bank-cand-pane-current")),J){const se=y.direction==="OUT"?"-":"+",ce=y.direction==="OUT"?"bank-out":"bank-in";J.innerHTML=`${N(j(y.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${N(y.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${se}${$(y.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const se=await fetch("/api/bank-recon/tx/"+encodeURIComponent(y.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!se.ok)throw new Error("cands:"+se.status);const ce=await se.json();ee(y,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function U(y){const F=Number(y||0);let O="score-low";return F>=85?O="score-high":F>=60&&(O="score-mid"),'<span class="bank-cand-score '+O+'">'+F.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Q(y,F,O){const J=F.history_id,X=F.invoice_no||"-",de=F.vendor||"-",se=F.amount_total!==null&&F.amount_total!==void 0?$(F.amount_total):"-",ce=F.invoice_date?j(F.invoice_date):"-",ae=F.filename||"",pe=!!O&&y.matched_history_id===J,fe="bank-cand-card"+(F.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let me="";return pe?me='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":me='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+N(J)+'"><span>'+t(F.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+fe+'" data-hid="'+N(J)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+N(de)+"</div>"+U(F.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+N(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+se+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+N(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+N(ae)+'">'+N(ae)+"</div>":"")+(F.reason?'<div class="bank-cand-card-reason">'+N(F.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+me+"</div></div>"}function ee(y,F){const O=document.getElementById("bank-cand-pane-body");if(!O)return;const J=F||[];let X="";if(y.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",J.length)+"</div>";else if(y.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",J.length)+"</div>";else if(J.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",J.length)+"</div>";else{O.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=y.match_status==="matched",se=J.map(ce=>Q(y,ce,de)).join("");O.innerHTML=X+'<div class="bank-cand-list">'+se+"</div>",O.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{S(ce.dataset.hid)})}),O.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(y.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const y=document.getElementById("bank-detail-body");y&&y.classList.remove("has-pane");const F=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),J=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");F&&(F.textContent=t("bank-cand-pane-empty-title")),O&&(O.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),J&&(J.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(se=>se.classList.remove("is-selected")),s=null}function oe(y){const F=document.getElementById("bank-upload-progress");F&&(F.style.display="none")}function ue(){const y=document.getElementById("bank-upload-error");y&&(y.style.display="none")}function x(y){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[y]||t("bank-err-unknown")+" ("+y+")"}function $(y){if(y==null)return"-";const F=Number(y);return isNaN(F)?"-":F.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function j(y){if(!y)return"-";const F=String(y);return F.length>=10?F.slice(0,10):F}function G(y,F){return!y&&!F?"":(j(y)||"?")+" ~ "+(j(F)||"?")}function N(y){return y==null?"":String(y).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=r,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(L(),n&&(K(),Z(),re(),!s)){const y=document.getElementById("bank-cand-pane-title"),F=document.getElementById("bank-cand-pane-sub");y&&(y.textContent=t("bank-cand-pane-empty-title")),F&&(F.textContent=t("bank-cand-pane-empty-sub"))}E()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(y){y&&(i||await r(),await d(y))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},i=new Set;let r=[];const p={keyword:""};let l=null;function d(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function f(w,R={}){const z=await fetch(w,{...R,headers:{"Content-Type":"application/json",...d(),...R.headers||{}}});if(!z.ok){const K=await z.json().catch(()=>({}));throw new Error(K.detail||"HTTP "+z.status)}return z.json()}async function c(){try{e=(await f("/api/clients")).clients||[],window._clientsCache=e}catch(w){console.error("loadClientsCache fail",w),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function u(w){o=w==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(K=>K.classList.toggle("active",K.dataset.custTab===o));const R=document.getElementById("cust-pane-seller"),z=document.getElementById("cust-pane-buyer");R&&R.classList.toggle("active",o==="seller"),z&&z.classList.toggle("active",o==="buyer")}function v(){const w=window._userInfo||{},R=String(w.role||"").toLowerCase(),z=String(w.tenant_role||"").toLowerCase();return w.is_super_admin===!0||w.is_owner===!0||R==="owner"||R==="admin"||z==="owner"||z==="admin"}function b(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function C(){try{const w=await f("/api/workspace/clients");r=w&&(w.clients||w.items)||[],window._workspaceClientsCache=r}catch(w){console.error("loadSellerCache fail",w),r=[]}return r}function E(){const w=p.keyword.trim().toLowerCase();return w?r.filter(R=>(R.name||"").toLowerCase().includes(w)||(R.tax_id||"").toLowerCase().includes(w)):r}function m(){const w=document.getElementById("seller-tbody");if(!w)return;const R=v(),z=document.getElementById("btn-seller-new");z&&(z.style.display=R?"":"none");const K=E(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!K.length){w.innerHTML=`<div class="cust-empty">${escapeHtml(t(p.keyword?"cust-no-match":"seller-empty"))}</div>`;return}w.innerHTML=K.map(le=>{const U=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Q=R?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${U}${Q}</div>
            </div>`}).join("")}function h(w){l=w?w.id:null,document.getElementById("wsclient-modal-title").textContent=t(w?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=w&&w.name||"",document.getElementById("wsclient-input-tax").value=w&&w.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=w?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function M(){document.getElementById("wsclient-modal-mask").style.display="none",l=null}async function B(){const w=document.getElementById("wsclient-input-name").value.trim(),R=document.getElementById("wsclient-input-tax").value.trim();if(!w){showToast(t("client-msg-name-required"),"fail");return}try{l?(await f("/api/workspace/clients/"+l,{method:"PATCH",body:JSON.stringify({name:w,tax_id:R})}),showToast(t("client-msg-updated"),"success")):(await f("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:w,tax_id:R||null})}),showToast(t("client-msg-created"),"success")),M(),await C(),m(),b()}catch(z){const K=z&&z.message?z.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+K,"fail")}}async function P(){if(!l)return;const w=r.find(z=>Number(z.id)===Number(l));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",w?w.name:""),{danger:!0}))try{const z=l;await f("/api/workspace/clients/"+z,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(z)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),M(),await C(),m(),b()}catch{showToast(t("client-msg-save-fail"),"fail")}}function H(){const w=s.keyword.trim().toLowerCase();return w?e.filter(R=>(R.name||"").toLowerCase().includes(w)||(R.short_name||"").toLowerCase().includes(w)||(R.tax_id||"").toLowerCase().includes(w)):e}function _(){const w=H(),R=s.pageSize,z=Math.max(0,Math.ceil(w.length/R)-1);s.page>z&&(s.page=z);const K=s.page*R;return{all:w,items:w.slice(K,K+R),start:K,ps:R,total:w.length,maxPage:z}}function g(){const w=document.getElementById("buyer-tbody");if(!w)return;const{items:R,start:z,ps:K,total:Z,maxPage:le}=_();Z?w.innerHTML=R.map(ee=>{const ne=i.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
                    <div class="cust-cell-check"><input type="checkbox" class="buyer-row-check" data-cid="${ee.id}" ${ne?"checked":""}></div>
                    <div style="min-width:0">
                        <div class="cust-cell-name"><span class="cust-color-dot" style="background:${escapeHtml(ee.color||"#111")}"></span><span class="cust-name-text">${escapeHtml(ee.name)}</span></div>
                        ${ee.tax_id?`<div class="cust-cell-sub">${escapeHtml(ee.tax_id)}</div>`:""}
                    </div>
                    <div class="align-right">${ee.invoice_count||0}</div>
                    <div class="align-right cust-cell-amount">฿${(ee.total_amount||0).toLocaleString(void 0,{maximumFractionDigits:0})}</div>
                    <div class="cust-row-actions">
                        <button class="cust-row-btn" data-action="edit" data-cid="${ee.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                        <button class="cust-row-btn" data-action="export" data-cid="${ee.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2v7M4 6l3 3 3-3M2 11h10"/></svg><span>${escapeHtml(t("client-card-export"))}</span></button>
                    </div>
                </div>`}).join(""):w.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Z?`${z+1}–${Math.min(z+K,Z)} / ${Z}`:"0");const U=document.getElementById("buyer-prev");U&&(U.disabled=s.page<=0);const Q=document.getElementById("buyer-next");Q&&(Q.disabled=s.page>=le),k()}function k(){const w=i.size,R=document.getElementById("buyer-batch-bar");R&&(R.style.display=w?"flex":"none");const z=document.getElementById("buyer-batch-count");z&&(z.textContent=t("cust-selected-n").replace("{n}",w));const K=document.getElementById("buyer-check-all");if(K){const{items:Z}=_(),le=Z.map(U=>U.id),ie=le.filter(U=>i.has(U)).length;K.checked=le.length>0&&ie===le.length,K.indeterminate=ie>0&&ie<le.length}}function S(){i.clear(),g()}async function T(){const w=Array.from(i);if(!(!w.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",w.length),{danger:!0})))try{await f("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:w})}),showToast(t("client-msg-deleted"),"success"),i.clear(),await c(),g(),te(),I()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const w=document.getElementById("seller-tbody");w&&(w.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const R=document.getElementById("buyer-tbody");R&&(R.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([C(),c()]),m(),g()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&m()});function q(w){n=w?w.id:null;const R=!!w;document.getElementById("client-modal-title").textContent=t(R?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=w&&w.name||"",document.getElementById("client-input-short").value=w&&w.short_name||"",document.getElementById("client-input-tax").value=w&&w.tax_id||"",document.getElementById("client-input-address").value=w&&w.address||"",document.getElementById("client-input-contact").value=w&&w.contact_person||"",document.getElementById("client-input-phone").value=w&&w.contact_phone||"",document.getElementById("client-input-email").value=w&&w.contact_email||"",document.getElementById("client-input-notes").value=w&&w.notes||"";const z=w&&w.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(K=>{K.classList.toggle("active",K.dataset.color===z)}),document.getElementById("client-modal-delete").style.display=R?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function L(){document.getElementById("client-modal-mask").style.display="none",n=null}function D(){const w=document.querySelector("#client-color-picker .color-swatch.active");return w?w.dataset.color:"#111111"}async function Y(){const w=document.getElementById("client-input-name").value.trim();if(!w){showToast(t("client-msg-name-required"),"fail");return}const R={name:w,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:D()};try{n?(await f(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(R)}),showToast(t("client-msg-updated"),"success")):(await f("/api/clients",{method:"POST",body:JSON.stringify(R)}),showToast(t("client-msg-created"),"success")),L(),await c(),currentRoute==="clients"&&g(),te(),I()}catch(z){console.error("saveClient fail",z);const K=z&&z.message?z.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+K,"fail")}}async function V(){if(!n)return;const w=e.find(K=>K.id===n);if(!w)return;const R=t("client-delete-confirm").replace("{name}",w.name);if(await showConfirm(R,{danger:!0}))try{await f(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),L(),await c(),currentRoute==="clients"&&g(),te(),I()}catch(K){console.error(K),showToast(t("client-msg-save-fail"),"fail")}}async function W(w){const R=e.find(z=>z.id===w);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(w,R?R.name:"");return}try{const z=localStorage.getItem("mrpilot_token"),K=await fetch(`/api/clients/${w}/export?month=all`,{headers:{Authorization:"Bearer "+z}});if(!K.ok){let Q="HTTP "+K.status;try{const ee=await K.json();ee&&ee.detail&&(Q=ee.detail)}catch{}throw new Error(Q)}const Z=await K.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=R&&R.name?R.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Z),U=document.createElement("a");U.href=ie,U.download=`${le}_export.csv`,U.click(),URL.revokeObjectURL(ie)}catch(z){console.error("exportClient fail",z),showToast(t("client-msg-save-fail")+" · "+(z.message||""),"fail")}}function te(){const w=document.getElementById("drawer-client-select");if(!w)return;const R=w.value;w.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(z=>`<option value="${z.id}">${escapeHtml(z.name)}</option>`).join(""),w.value=R||""}window.bindDrawerClient=function(w,R){const z=document.getElementById("drawer-client-select");if(!z)return;if(te(),z.value=R?String(R):"",!w){z.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>q(null));return}z.onchange=async()=>{const Z=z.value?parseInt(z.value,10):null;try{await f(`/api/history/${w}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await c()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),z.value=R?String(R):""}};const K=document.getElementById("drawer-client-add");K&&(K.onclick=()=>q(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const w=document.getElementById("drawer-cat-datalist"),R=Date.now();if(R-re.fetched<300*1e3){w&&(w.innerHTML=re.items.map(K=>`<option value="${escapeHtml(K)}">`).join("")),A(re.supplier_count);return}const z=await f("/api/categories",{method:"GET"});re.fetched=R,re.items=z&&z.categories||[],re.supplier_count=z&&z.supplier_count||0,w&&(w.innerHTML=re.items.map(K=>`<option value="${escapeHtml(K)}">`).join("")),A(re.supplier_count)}catch(w){console.warn("fillCategoryDatalist failed",w)}};function A(w){const R=document.getElementById("drawer-cat-learned-tag");R&&w>0&&(R.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",w))}function I(){const w=document.getElementById("history-client-filter");if(!w)return;const R=w.value;w.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(z=>`<option value="${z.id}">${escapeHtml(z.name)}</option>`).join(""),w.value=R||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const w=document.querySelector(".cust-tab-bar");w&&w.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&u(pe.dataset.custTab)});const R=document.getElementById("btn-buyer-new");R&&R.addEventListener("click",()=>q(null));const z=document.getElementById("buyer-tbody");z&&z.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?i.add(ge):i.delete(ge);const ye=pe.closest(".cust-row");ye&&ye.classList.toggle("selected",pe.checked),k();return}const fe=ae.target.closest(".cust-row-btn");if(fe){ae.stopPropagation();const ge=parseInt(fe.dataset.cid,10);if(fe.dataset.action==="edit"){const ye=e.find(xe=>xe.id===ge);ye&&q(ye)}else fe.dataset.action==="export"&&W(ge);return}const me=ae.target.closest(".cust-row");if(me&&!ae.target.closest(".cust-cell-check")){const ge=e.find(ye=>ye.id===parseInt(me.dataset.cid,10));ge&&q(ge)}});const K=document.getElementById("buyer-check-all");K&&K.addEventListener("change",()=>{const{items:ae}=_();ae.forEach(pe=>{K.checked?i.add(pe.id):i.delete(pe.id)}),g()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",S);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",T);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{s.page>0&&(s.page--,g())});const U=document.getElementById("buyer-next");U&&U.addEventListener("click",()=>{s.page++,g()});const Q=document.getElementById("buyer-search");if(Q){let ae;Q.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{s.keyword=Q.value,s.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Q.value?"":"none"),g()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),s.keyword="",s.page=0,ee.style.display="none",g()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>h(null));const oe=document.getElementById("seller-tbody");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const fe=parseInt(pe.dataset.wid,10),me=pe.dataset.saction,ge=r.find(ye=>Number(ye.id)===fe);me==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(fe),m(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):me==="edit"?ge&&h(ge):me==="archive"&&(l=fe,P())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{p.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),m()},200)})}const x=document.getElementById("seller-search-clear");x&&x.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),p.keyword="",x.style.display="none",m()});const $=document.getElementById("wsclient-modal-close");$&&$.addEventListener("click",M);const j=document.getElementById("wsclient-modal-cancel");j&&j.addEventListener("click",M);const G=document.getElementById("wsclient-modal-save");G&&G.addEventListener("click",B);const N=document.getElementById("wsclient-modal-archive");N&&N.addEventListener("click",P);const y=document.getElementById("wsclient-modal-mask");y&&y.addEventListener("click",ae=>{ae.target===y&&M()});const F=document.getElementById("client-modal-close");F&&F.addEventListener("click",L);const O=document.getElementById("client-modal-cancel");O&&O.addEventListener("click",L);const J=document.getElementById("client-modal-save");J&&J.addEventListener("click",Y);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",V);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&L()});const se=document.getElementById("client-color-picker");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(se.querySelectorAll(".color-swatch").forEach(fe=>fe.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>c(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(A,I){let w=t(A)||A;if(I)for(const R in I)w=w.replace(new RegExp("\\{"+R+"\\}","g"),String(I[R]));return w}async function a(){try{const A=e.currentClient||"",I="/api/exceptions/stats?status=pending"+(A?"&client_id="+encodeURIComponent(A):""),w=await fetch(I,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!w.ok)return;const R=await w.json(),z=document.getElementById("nav-exc-badge");if(!z)return;const K=parseInt(R.pending||0,10);K>0?(z.textContent=K>99?"99+":String(K),z.style.display=""):z.style.display="none"}catch{}}function o(A){return A==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:A==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function s(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function i(A){if(A==null)return"—";const I=parseFloat(A);return isNaN(I)?"—":"฿ "+I.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function r(A){return A?A.slice(0,10):"—"}function p(A){document.getElementById("exc-kpi-pending").textContent=A.pending||0,document.getElementById("exc-kpi-high").textContent=A.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=A.resolved||0,document.getElementById("exc-kpi-learned").textContent=A.learned_rules||0;const I=document.getElementById("exc-status-tab-count-pending"),w=document.getElementById("exc-status-tab-count-resolved"),R=document.getElementById("exc-status-tab-count-ignored");I&&(I.textContent=A.pending||0),w&&(w.textContent=A.resolved||0),R&&(R.textContent=A.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(K=>{K.classList.toggle("active",K.dataset.status===(e.currentStatus||"pending"))})}function l(A){const I=document.getElementById("exc-chips");if(!I)return;const w=A.by_rule||{},R=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let K=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${A.pending||0}</span>
        </button>`;for(const Z of R){const le=w[Z]||0;if(le===0&&e.currentRule!==Z)continue;const ie=e.currentRule===Z;K+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}I.innerHTML=K,I.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,b()})})}function d(A){const I=document.getElementById("exc-list");if(!I)return;if(!A||A.length===0){I.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,c();return}const w='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',R=(e.currentStatus||"pending")==="pending";I.innerHTML=A.map(z=>{const K=z.severity||"medium",Z=t("exc-rule-"+z.rule_code)||z.rule_code,le=z.seller_name&&z.seller_name.trim()?z.seller_name:t("exc-no-seller"),ie=z.filename||"—",U=r(z.invoice_date||z.created_at),Q=z.status==="pending",ee=e.selectedIds.has(z.id),ne=R&&Q;return`
                <div class="exc-row sev-${escapeHtml(K)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(z.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(z.id))}" ${ne?"":'style="visibility:hidden;"'}>${w}</div>
                    <div class="exc-row-sev">${o(K)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${z.invoice_no?`<span><b>${escapeHtml(z.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(U)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(K)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(i(z.total_amount))}</div>
                </div>
            `}).join(""),I.querySelectorAll(".exc-row").forEach(z=>{z.addEventListener("click",K=>{if(K.target.closest(".exc-row-check"))return;const Z=z.dataset.excId;Z&&B(parseInt(Z,10))})}),I.querySelectorAll(".exc-row-check").forEach(z=>{z.addEventListener("click",K=>{K.stopPropagation();const Z=parseInt(z.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),z.classList.remove("checked"),z.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),z.classList.add("checked"),z.closest(".exc-row").classList.add("selected")),f())})}),f(),c()}function f(){const A=document.getElementById("exc-batch-bar"),I=document.getElementById("exc-batch-count");if(!A||!I)return;const w=e.selectedIds.size;w===0?A.style.display="none":(A.style.display="",I.textContent=n("exc-batch-count",{n:w}))}function c(){const A=document.getElementById("exc-list-foot"),I=document.getElementById("exc-list-count"),w=document.getElementById("exc-loadmore");if(!A||!I||!w)return;const R=e.listCache.length;if(R===0){A.style.display="none";return}A.style.display="";let z=R;const K=e.statsCache;K&&(e.currentRule?z=(K.by_rule||{})[e.currentRule]||R:z=K.pending||R),e.total=z,I.textContent=n("exc-list-count",{shown:R,total:z});const Z=R<z&&R<500;w.style.display=Z?"":"none"}async function u(){try{if(navigator.onLine===!1)throw new Error("offline");const A=e.currentClient||"",I=e.currentStatus||"pending",w=new URLSearchParams;w.set("status",I),A&&w.set("client_id",A);const R="/api/exceptions/stats?"+w.toString(),z=await fetch(R,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!z.ok)throw new Error("http "+z.status);const K=await z.json();return e.statsCache=K,p(K),l(K),K}catch(A){return console.warn("loadExceptionsStats fail",A),null}}function v(A){const I=document.getElementById("exc-list");if(!I)return;const w=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,R=A?t("exc-offline"):t("exc-error-retry-title"),z=A?"":t("exc-error-retry-desc");I.innerHTML=`
            <div class="exc-error">
                ${w}
                <div class="exc-error-msg">${escapeHtml(R)}${z?" · "+escapeHtml(z):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const K=document.getElementById("exc-retry-btn");K&&K.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function b(A){A=A||{};const I=!!A.append,w=document.getElementById("exc-list");!I&&w&&e.listCache.length===0&&(w.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const R=new URLSearchParams;R.set("status",e.currentStatus||"pending"),e.currentRule&&R.set("rule_code",e.currentRule),e.currentClient&&R.set("client_id",e.currentClient);const z=I?e.listCache.length:0;R.set("limit",String(e.pageSize)),R.set("offset",String(z));try{if(navigator.onLine===!1)throw new Error("offline");const K=await fetch("/api/exceptions/list?"+R.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!K.ok)throw new Error("http "+K.status);const le=(await K.json()).items||[];I?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,d(e.listCache),e.statsCache&&l(e.statsCache)}catch(K){console.warn("loadExceptionsList fail",K),e.loadFailed=!0;const Z=navigator.onLine===!1||String(K.message||"").includes("offline");I?showToast(t("exc-toast-load-fail"),"error"):(v(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function C(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await b({append:!0})}finally{e.loading=!1}}}function E(){const A=document.getElementById("exc-client-filter");if(!A)return;const I=window._clientsCache||[],w=e.currentClient||"",R=typeof t=="function"?t("history-client-all"):"全部客户";A.innerHTML=`<option value="">${escapeHtml(R)}</option>`+I.map(z=>`<option value="${z.id}">${escapeHtml(z.name)}</option>`).join(""),A.value=w}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{E(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await u(),await b()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=E,window._excState=e,window._rerenderExceptions=function(){try{E()}catch{}e.statsCache&&(p(e.statsCache),l(e.statsCache)),e.listCache&&e.listCache.length&&d(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}m.openExcId&&S()};let m={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function h(){if(m.pdfUrl){try{URL.revokeObjectURL(m.pdfUrl)}catch{}m.pdfUrl=null}m.pdfStatus="idle"}async function M(A,I){m.pdfStatus="loading",S();try{const w=await fetch("/api/history/"+encodeURIComponent(A)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(m.openExcId!==I)return;if(w.status===404){m.pdfStatus="empty",S();return}if(!w.ok)throw new Error("http "+w.status);const R=await w.blob();if(m.openExcId!==I)return;h(),m.pdfUrl=URL.createObjectURL(R),m.pdfStatus="ready",S()}catch(w){if(m.openExcId!==I)return;console.warn("loadDrawerPdf fail",w),m.pdfStatus="error",S()}}function B(A){const I=(e.listCache||[]).find(w=>w.id===A);if(!I){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,h(),m.editing=!1,m.editFields=null,m.openExcId=A,m.excRow=I,m.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),S(),H(I.history_id),M(I.history_id,A)}function P(){h(),m.editing=!1,m.editFields=null,m.openExcId=null,m.excRow=null,m.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const A=e.listScrollY||0;A>0&&requestAnimationFrame(()=>window.scrollTo(0,A))}async function H(A){try{const I=await fetch("/api/history/"+encodeURIComponent(A),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!I.ok)throw new Error("http "+I.status);m.history=await I.json()}catch(I){console.warn("loadHistoryDetail fail",I),m.history={_err:!0}}m.excRow&&S()}function _(A){if(!A||!A.pages)return{};const I=A.pages,w=I.find(R=>!R.is_duplicate&&!R.is_copy)||I[0];return w&&w.fields||{}}function g(A){if(A==null)return"—";const I=typeof A=="number"?A:parseFloat(String(A).replace(/,/g,""));return isNaN(I)?escapeHtml(String(A)):"฿ "+I.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function k(A,I){if(I=I||{},A==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(g(I.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(g(I.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(g(I.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(g(I.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(g(I.diff))}</span></div>
            `;if(A==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(I.tax_id_normalized||I.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(I.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(A==="duplicate"){const w=I.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(I.match_filename||"—")}</span></div>
                ${I.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(I.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(w)}</span></div>
            `}return A==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(I.confidence||"—")}</span></div>
            `:A==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(I))}</span></div>`}function S(){const A=m.excRow;if(!A)return;const I=A.seller_name&&A.seller_name.trim()?A.seller_name:t("exc-no-seller"),w=A.filename||"—";document.getElementById("exc-drawer-title").textContent=w;const R="exc-status-"+(A.status||"pending"),z=t(R)||A.status,K="s-"+(A.status||"pending"),Z=(A.invoice_date||A.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(I)}</span>
            ${A.invoice_no?`<span>· ${escapeHtml(A.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${K}">${escapeHtml(z)}</span>
        `;const le=A.severity||"medium",ie=t("exc-rule-"+A.rule_code)||A.rule_code,U=k(A.rule_code,A.detail||{}),Q=_(m.history),ee=m.history===null,ne=m.history&&m.history._err,oe=new Set;A.rule_code==="math_mismatch"?(oe.add("subtotal"),oe.add("vat"),oe.add("total_amount")):A.rule_code==="tax_id_format_invalid"?oe.add("seller_tax"):A.rule_code==="amount_missing"&&(oe.add("total_amount"),oe.add("invoice_number"));const ue=!!m.editing,x=m.editFields||{},$=(ae,pe,fe)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const me=ue?x[ae]!==void 0?x[ae]:Q[ae]!==void 0&&Q[ae]!==null?Q[ae]:"":Q[ae],ge=oe.has(ae)?"flagged":"";if(ue){const Ne=fe?"number":"text",Te=fe?' step="0.01" inputmode="decimal"':"",He=me==null?"":String(me).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${Ne}"${Te} data-edit-key="${escapeHtml(ae)}" value="${He}">
                </div>`}const ye=fe?g(me):me||"",xe=me==null||me===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(ye)}</span>`;return`<div class="exc-field-row ${ge}"><label>${escapeHtml(t(pe))}</label>${xe}</div>`};let j="";ne?j=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:j=`
                <div class="exc-fields">
                    ${$("invoice_number","exc-fld-invoice-no",!1)}
                    ${$("date","exc-fld-date",!1)}
                    ${$("seller_name","exc-fld-seller",!1)}
                    ${$("seller_tax","exc-fld-seller-tax",!1)}
                    ${$("buyer_name","exc-fld-buyer",!1)}
                    ${$("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${$("subtotal","exc-fld-subtotal",!0)}
                    ${$("vat","exc-fld-vat",!0)}
                    ${$("total_amount","exc-fld-total",!0)}
                </div>
            `;const G=(()=>{if(m.pdfStatus==="loading"||m.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(m.pdfStatus==="empty")return`
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
                `;if(m.pdfStatus==="error")return`
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
                `;const ae=m.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(w)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(w)}" title="${escapeHtml(t("exc-pdf-download"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${ae}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `})();document.getElementById("exc-drawer-body").innerHTML=`
            <div class="exc-pdf-pane">${G}</div>
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
                        <div class="exc-why-rule">${escapeHtml(ie)}</div>
                        <div class="exc-why-detail">${U}</div>
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
                        ${A.status==="pending"&&!ee&&!ne?ue?`
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
        `;const N=document.getElementById("exc-fld-edit");N&&N.addEventListener("click",()=>{m.editing=!0,m.editFields={..._(m.history)},S()});const y=document.getElementById("exc-fld-cancel");y&&y.addEventListener("click",()=>{m.editing=!1,m.editFields=null,S()});const F=document.getElementById("exc-fld-save");F&&F.addEventListener("click",()=>T()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{m.editFields||(m.editFields={}),m.editFields[ae.dataset.editKey]=ae.value})});const J=document.getElementById("exc-pdf-retry");J&&m.openExcId&&J.addEventListener("click",()=>{m.excRow&&M(m.excRow.history_id,m.openExcId)});const X=A.status==="pending",de=!!(A.seller_name&&A.seller_name.trim()),se=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");se.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function T(){if(!m.openExcId||!m.history||!m.history.pages||m.loading)return;m.loading=!0;const A=showToast(t("exc-fld-saving"),"loading",0);try{const I=JSON.parse(JSON.stringify(m.history.pages||[]));let w=I.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);w<0&&(w=0),I[w]||(I[w]={fields:{}});const R=I[w].fields||{},z=m.editFields||{},K=new Set(["subtotal","vat","total_amount"]),Z={...R};for(const ie in z){let U=z[ie];if((U===""||U===void 0)&&(U=null),K.has(ie)&&U!==null){const Q=parseFloat(U);U=isNaN(Q)?null:Q}Z[ie]=U}I[w].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(m.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:I})});if(!le.ok)throw new Error("http "+le.status);A(),showToast(t("exc-fld-save-ok"),"success"),P(),await u(),await b(),a()}catch(I){A(),console.warn("save fields fail",I),showToast(t("exc-fld-save-fail"),"error")}finally{m.loading=!1}}async function q(){if(!(!m.openExcId||m.loading)){m.loading=!0;try{const A=await fetch("/api/exceptions/"+m.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!A.ok)throw new Error("http "+A.status);showToast(t("exc-toast-resolved"),"success"),P(),await u(),await b(),a()}catch(A){console.warn("resolve fail",A),showToast(t("exc-toast-action-fail"),"error")}finally{m.loading=!1}}}async function L(){if(!(!m.openExcId||m.loading)){m.loading=!0;try{const A=await fetch("/api/exceptions/"+m.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!A.ok)throw new Error("http "+A.status);showToast(t("exc-toast-ignored"),"success"),P(),await u(),await b(),a()}catch(A){console.warn("ignore fail",A),showToast(t("exc-toast-action-fail"),"error")}finally{m.loading=!1}}}let D=!1;async function Y(){if(D)return;const A=Array.from(e.selectedIds);if(A.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:A.length})))return;D=!0;const w=showToast(n("exc-batch-count",{n:A.length})+" …","loading",0);try{const R=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:A,action:"resolve"})});if(!R.ok)throw new Error("http "+R.status);const z=await R.json();w(),showToast(n("exc-toast-batch-resolved",{n:z.processed||0}),"success"),e.selectedIds.clear(),await u(),await b(),a()}catch(R){w(),console.warn("batch resolve fail",R),showToast(t("exc-toast-batch-fail"),"error")}finally{D=!1}}async function V(){if(D)return;const A=Array.from(e.selectedIds);if(A.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:A.length}),{danger:!1}))return;D=!0;const w=showToast(n("exc-batch-count",{n:A.length})+" …","loading",0);try{const R=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:A,action:"ignore"})});if(!R.ok)throw new Error("http "+R.status);const z=await R.json();w(),showToast(n("exc-toast-batch-ignored",{n:z.processed||0,wl:z.whitelist_added||0}),"success"),e.selectedIds.clear(),await u(),await b(),a()}catch(R){w(),console.warn("batch ignore fail",R),showToast(t("exc-toast-batch-fail"),"error")}finally{D=!1}}function W(){e.selectedIds.clear(),d(e.listCache)}document.addEventListener("click",A=>{A.target.closest("#exc-drawer-close")&&P(),A.target.closest("#exc-drawer-mask")&&P(),A.target.closest("#exc-btn-resolve")&&q(),A.target.closest("#exc-btn-ignore")&&L(),A.target.closest("#exc-batch-resolve")&&Y(),A.target.closest("#exc-batch-ignore")&&V(),A.target.closest("#exc-batch-clear")&&W(),A.target.closest("#exc-loadmore")&&C()}),document.addEventListener("keydown",A=>{A.key==="Escape"&&m.openExcId&&P()}),document.addEventListener("click",A=>{A.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",A=>{if(!A.target.closest("#exc-client-filter"))return;const I=A.target;e.currentClient=I.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",A=>{const I=A.target.closest("#exc-status-tabs .exc-status-tab");if(!I)return;const w=I.dataset.status||"pending";w!==e.currentStatus&&(e.currentStatus=w,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function te(A){if(!A)return"—";try{const I=new Date(A),w=R=>String(R).padStart(2,"0");return`${I.getFullYear()}-${w(I.getMonth()+1)}-${w(I.getDate())} ${w(I.getHours())}:${w(I.getMinutes())}`}catch{return A.slice(0,16).replace("T"," ")}}async function re(){const A=document.getElementById("learned-list");if(A){A.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const I=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!I.ok)throw new Error("http "+I.status);const R=(await I.json()).items||[];if(R.length===0){A.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const z=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;A.innerHTML=R.map(K=>{const Z=t("exc-rule-"+K.rule_code)||K.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(K.id))}">
                        <div class="learned-seller" title="${escapeHtml(K.seller_name)}">${escapeHtml(K.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(te(K.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(K.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${z}</button>
                    </div>
                `}).join("")}catch(I){console.warn("loadLearnedRules fail",I),A.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async A=>{const I=A.target.closest("[data-del-wl]");if(!I)return;const w=parseInt(I.dataset.delWl,10);if(!w)return;const R=I.closest(".learned-row"),z=R&&R.querySelector(".learned-seller"),K=z?z.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",K);if(await showConfirm(Z,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+w,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(c){const u=typeof currentLang=="string"&&currentLang||window._currentLang||"th",v=c.error_friendly&&c.error_friendly[u];if(v)return v;if(typeof humanizeError=="function"&&c.error_msg)try{return humanizeError(c.error_msg)}catch{}return t("erp-exc-reason-"+(c.category||"other"))}function s(){const c=document.getElementById("erp-exc-batch");if(!c)return;const u=e.selected.size;c.hidden=u===0;const v=c.querySelector(".erp-exc-batch-count");v&&(v.textContent=String(u))}function i(){const c=document.getElementById("erp-exc-block");if(!c)return;const u=e;if(!(u.total>0||!!u.q||!!u.cat)){c.hidden=!0,c.innerHTML="";return}c.hidden=!1;const b=u.categories||{},C=Object.keys(b).reduce((k,S)=>k+b[S],0);let E=`<button class="erp-exc-chip ${u.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${C}</span></button>`;Object.keys(b).forEach(k=>{E+=`<button class="erp-exc-chip ${u.cat===k?"active":""}" data-erpexc-cat="${escapeHtml(k)}"><span>${escapeHtml(t("erp-exc-cat-"+k))}</span><span class="erp-exc-chip-count">${b[k]}</span></button>`});const m=u.items||[],h=m.length>0&&m.every(k=>u.selected.has(k.id)),M=m.map(k=>{const S=k.state==="needs_action"?"needs":k.state==="retrying"?"retry":"fail",T=t("erp-exc-state-"+(k.state||"failed")),q=o(k),L=u.selected.has(k.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(k.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(k.id)}" ${L}></span>
                <span class="ex-inv" title="${escapeHtml(k.invoice_no||"")}">${escapeHtml(k.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(k.seller_name||"")}">${escapeHtml(k.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(k.ocr_buyer_name||"")}">${escapeHtml(k.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${S}">${escapeHtml(T)}</span></span>
                <span class="ex-reason" title="${escapeHtml(q)}">${escapeHtml(q)}${k.error_code?` <span class="erp-exc-code">${escapeHtml(k.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(k.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),B=m.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",P=m.length<u.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${m.length}/${u.total})</button>`:u.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:m.length,total:u.total}))}</div>`:"";c.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
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
                    <span class="ex-inv">${escapeHtml(t("erp-exc-f-invoice"))}</span>
                    <span class="ex-seller">${escapeHtml(t("erp-exc-f-seller"))}</span>
                    <span class="ex-buyer">${escapeHtml(t("erp-exc-f-buyer"))}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${M}${B}
            </div>
            <div class="erp-exc-foot">${P}</div>`;const H=document.getElementById("erp-exc-search");if(H){if(u.focusSearch){H.focus();try{H.setSelectionRange(u.searchCaret,u.searchCaret)}catch{}}H.addEventListener("input",()=>{u.q=H.value,u.focusSearch=!0,u.searchCaret=H.selectionStart||H.value.length,clearTimeout(n),n=setTimeout(()=>l(!1),350)}),H.addEventListener("blur",()=>{u.focusSearch=!1})}c.querySelectorAll(".erp-exc-chip").forEach(k=>{k.addEventListener("click",()=>{u.cat=k.dataset.erpexcCat||"",l(!1)})}),c.querySelectorAll("[data-erpexc-retry]").forEach(k=>{k.addEventListener("click",S=>{S.stopPropagation(),r(k.dataset.erpexcRetry,k)})}),c.querySelectorAll(".erp-exc-cb").forEach(k=>{k.addEventListener("change",()=>{const S=k.dataset.erpexcCb;k.checked?u.selected.add(S):u.selected.delete(S);const T=document.getElementById("erp-exc-cb-all");T&&(T.checked=m.length>0&&m.every(q=>u.selected.has(q.id))),s()})});const _=document.getElementById("erp-exc-cb-all");_&&_.addEventListener("change",()=>{m.forEach(k=>{_.checked?u.selected.add(k.id):u.selected.delete(k.id)}),c.querySelectorAll(".erp-exc-cb").forEach(k=>{k.checked=_.checked}),s()}),c.querySelectorAll("[data-erpexc-batch]").forEach(k=>{k.addEventListener("click",()=>p(k.dataset.erpexcBatch))});const g=document.getElementById("erp-exc-more");g&&g.addEventListener("click",()=>l(!0)),c.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(k=>{k.addEventListener("click",S=>{S.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(k.dataset.erpexcId)})})}async function r(c,u){if(c){u&&(u.disabled=!0,u.textContent=t("erp-exc-retrying"));try{const v=await fetch("/api/erp/logs/"+encodeURIComponent(c)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),b=await v.json().catch(()=>({}));showToast(v.ok&&b.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),v.ok&&b.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(c),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function p(c){const u=Array.from(e.selected);if(c==="clear"){e.selected.clear(),i();return}if(u.length!==0){if(c==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:u.length}),{danger:!0}))return;try{const b=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,200)})}),C=await b.json().catch(()=>({}));showToast(b.ok?t("erp-exc-batch-delete-ok",{n:C.deleted||0}):t("erp-exc-retry-fail"),b.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(c==="retry")try{const v=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:u.slice(0,50)})}),b=await v.json().catch(()=>({}));showToast(v.ok?t("erp-exc-batch-retry-ok",{ok:b.succeeded||0,fail:(b.failed||0)+(b.skipped||0)}):t("erp-exc-retry-fail"),v.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function l(c){const u=document.getElementById("erp-exc-block");if(!(!u||e.loading)){e.loading=!0;try{const v=new URLSearchParams;e.q&&v.set("q",e.q),e.cat&&v.set("category",e.cat),v.set("limit",String(e.pageSize)),v.set("offset",String(c?e.items.length:0));const b=await fetch("/api/erp/exceptions?"+v.toString(),{headers:{Authorization:"Bearer "+a()}});if(!b.ok){c||(u.hidden=!0);return}const C=await b.json(),E=C.items||[];e.items=c?e.items.concat(E):E,e.total=C.total||0,e.categories=C.categories||{},i()}catch{c||(u.hidden=!0)}finally{e.loading=!1}}}let d={};function f(){const c=document.getElementById("erp-exc-modal");c&&c.remove()}window._erpExcOpenEdit=function(c){const u=(e.items||[]).find(B=>String(B.id)===String(c));if(!u)return;const v=!!u.history_client_id&&u.category==="customer_mismatch",b=u.category==="product_mismatch"&&!!u.history_id&&!!u.endpoint_id,C=o(u),E=u.state==="needs_action"?"needs":u.state==="retrying"?"retry":"fail",m=(B,P)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(B)}</span><span class="erp-exc-m-v">${escapeHtml(P||"—")}</span></div>`;let h="";if(v)h=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(b)h=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const B="erp-exc-edit-hint-"+(u.category||"other");let P=t(B);(!P||P===B)&&(P=C),h=`<div class="erp-exc-m-hint">${escapeHtml(P)}</div>`}const M=document.createElement("div");if(M.id="erp-exc-modal",M.className="erp-exc-modal-overlay",M.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${E}">${escapeHtml(t("erp-exc-state-"+(u.state||"failed")))}</span> ${escapeHtml(C)}${u.error_code?` <span class="erp-exc-code">${escapeHtml(u.error_code)}</span>`:""}</div>
                    ${m(t("erp-exc-f-invoice"),u.invoice_no)}
                    ${m(t("erp-exc-f-seller"),u.seller_name)}
                    ${m(t("erp-exc-f-buyer"),u.ocr_buyer_name)}
                    ${m(t("erp-exc-edit-field-current"),u.client_name)}
                    ${h}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${v?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${b?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild(M),M.addEventListener("click",B=>{B.target===M&&f()}),document.getElementById("erp-exc-m-close").addEventListener("click",f),document.getElementById("erp-exc-m-cancel").addEventListener("click",f),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{f(),r(u.id,null)}),v){let B="";const P=document.getElementById("erp-exc-m-bind"),H=document.getElementById("erp-exc-m-custlist"),_=document.getElementById("erp-exc-m-search"),g=(S,T)=>{const q=(T||"").trim().toLowerCase(),L=q?S.filter(D=>(D.code||"").toLowerCase().includes(q)||(D.name||"").toLowerCase().includes(q)):S;if(L.length===0){H.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}H.innerHTML=L.slice(0,100).map(D=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(D.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(D.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(D.code||"")}</span>
                    </div>`).join(""),H.querySelectorAll(".erp-exc-m-cust").forEach(D=>{D.addEventListener("click",()=>{B=D.dataset.custCode||"",H.querySelectorAll(".erp-exc-m-cust").forEach(Y=>Y.classList.remove("sel")),D.classList.add("sel"),P&&(P.disabled=!B)})})},k=async()=>{const S=u.endpoint_id;if(d[S]){g(d[S],"");return}try{const T=await fetch("/api/erp/endpoints/"+encodeURIComponent(S)+"/customers",{headers:{Authorization:"Bearer "+a()}}),q=await T.json().catch(()=>({}));if(!T.ok||!q.ok){H.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const L=q.customers||[];d[S]=L,g(L,"")}catch{H.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};_&&_.addEventListener("input",()=>g(d[u.endpoint_id]||[],_.value)),k(),P&&P.addEventListener("click",async()=>{if(B){P.disabled=!0,P.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:u.history_client_id,erp_type:u.endpoint_adapter,erp_code:B})})).ok){showToast(t("erp-exc-retry-fail"),"error"),P.disabled=!1,P.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),f(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),P.disabled=!1,P.textContent=t("erp-exc-edit-bind-retry")}}})}if(b){const B=document.getElementById("erp-exc-m-bind-prod"),P=document.getElementById("erp-exc-m-prodlist"),H={};let _=[];const g=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+_.slice(0,500).map(T=>`<option value="${escapeHtml(T.code||"")}" data-pname="${escapeHtml(T.name||"")}">`+escapeHtml((T.name||"")+" · "+(T.code||""))+"</option>").join(""),k=T=>{if(!T.length){P.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}P.innerHTML=T.map(q=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(q)}">${escapeHtml(q)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(q)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${g()}</select>
                    </div>`).join(""),P.querySelectorAll(".erp-exc-m-prod-sel").forEach(q=>{q.addEventListener("change",()=>{const L=q.dataset.item,D=q.options[q.selectedIndex];q.value?H[L]={code:q.value,name:D&&D.dataset.pname||""}:delete H[L],B&&(B.disabled=Object.keys(H).length===0)})})};(async()=>{try{const q=await(await fetch("/api/history/"+encodeURIComponent(u.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),L=q&&q.pages||[],D=[],Y={};(Array.isArray(L)?L:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(A=>{const I=(A&&(A.name||A.description)||"").trim();I&&!Y[I]&&(Y[I]=1,D.push(I))})});const V=await fetch("/api/erp/endpoints/"+encodeURIComponent(u.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),W=await V.json().catch(()=>({}));if(!V.ok||!W.ok){P.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}_=W.products||[],k(D)}catch{P.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),B&&B.addEventListener("click",async()=>{const T=Object.entries(H);if(T.length){B.disabled=!0,B.textContent=t("erp-exc-retrying");try{for(const[q,L]of T)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:u.endpoint_adapter,item_name:q,erp_code:L.code,erp_name:L.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),B.disabled=!1,B.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),f(),await r(u.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),B.disabled=!1,B.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=l,window._erpExcState=e})();(function(){function e(c){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||c&&c.id&&String(c.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var u=window._userInfo,v=!1,b=!0,C=!1,E=!1;u&&(v=typeof canManageTeam=="function"?canManageTeam(u):!!(u.role==="owner"||u.is_super_admin),b=typeof shouldHideMoney=="function"?shouldHideMoney(u):u.role==="member"&&!u.is_super_admin,C=typeof isSuperAdmin=="function"?isSuperAdmin(u):!!u.is_super_admin,E=e(u)),document.querySelectorAll("[data-show-if-team]").forEach(function(h){h.style.display=v?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(h){h.style.display=b?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(h){h.style.display=C?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(h){h.style.display=E?"":"none"});var m=C||E;document.querySelectorAll("[data-show-if-special]").forEach(function(h){h.style.display=m?"":"none"})},window.renderAvatarMenu=function(u){if(u){var v=document.getElementById("avatar-btn"),b=document.getElementById("avatar-popup-name"),C=document.getElementById("avatar-popup-email");if(!(!v||!b||!C)){var E=(u.username||"").trim(),m=E.split("@")[0]||E||"—",h=(E.charAt(0)||"?").toUpperCase(),M=(u.avatar_url||"").trim();if(M){var B=M.replace(/"/g,"&quot;"),P=h.replace(/'/g,"\\'");v.innerHTML='<img src="'+B+'" alt="'+h+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+P+`'">`}else v.textContent=h;b.textContent=m,C.textContent=E||"—",v.setAttribute("title",E||"")}}};function n(){var c=document.getElementById("avatar-wrap"),u=document.getElementById("avatar-btn"),v=document.getElementById("avatar-popup");if(!c||!u||!v)return;function b(){v.classList.remove("show"),u.setAttribute("aria-expanded","false")}function C(){v.classList.add("show"),u.setAttribute("aria-expanded","true")}u.addEventListener("click",function(E){E.stopPropagation(),v.classList.contains("show")?b():C()}),document.addEventListener("click",function(E){v.classList.contains("show")&&!c.contains(E.target)&&b()}),v.addEventListener("click",function(E){var m=E.target.closest(".avatar-popup-item");if(m){var h=m.dataset.action;switch(b(),h){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var M=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(M||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var B=document.getElementById("help-modal");B&&(B.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=b}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(c){return c.style.display!=="none"})}function o(c){var u=a();u.forEach(function(v){v.classList.remove("focus")}),u[c]&&(u[c].classList.add("focus"),u[c].scrollIntoView({block:"nearest"}))}function s(c){var u=a();if(u.length){var v=u.findIndex(function(C){return C.classList.contains("focus")});v<0&&(v=0);var b=(v+c+u.length)%u.length;o(b)}}function i(c){c=(c||"").toLowerCase().trim();var u=0,v=window._userInfo,b=typeof isSuperAdmin=="function"?isSuperAdmin(v):!!(v&&v.is_super_admin),C=e(v);document.querySelectorAll(".cmdk-item").forEach(function(m){if(m.dataset.showIfAdmin==="1"&&!b){m.style.display="none";return}if(m.dataset.showIfTest==="1"&&!C){m.style.display="none";return}var h=(m.dataset.cmdkText||m.textContent||"").toLowerCase(),M=!c||h.indexOf(c)>=0;m.style.display=M?"":"none",m.classList.remove("focus"),M&&u++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(m){for(var h=m.nextElementSibling,M=!1;h&&!h.hasAttribute("data-cmdk-section");){if(h.classList&&h.classList.contains("cmdk-item")&&h.style.display!=="none"){M=!0;break}h=h.nextElementSibling}m.style.display=M?"":"none"});var E=document.getElementById("cmdk-empty");E&&(E.style.display=u===0?"flex":"none"),o(0)}window.openCmdk=function(){var u=document.getElementById("cmdk-mask");u&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),u.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var v=document.getElementById("cmdk-input");v&&(v.value="",i(""),v.focus(),o(0))},50))},window.closeCmdk=function(){var u=document.getElementById("cmdk-mask");u&&u.classList.remove("show")};function r(c){if(c){if(c.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var u=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(u||"即将上线","info")}return}var v=c.dataset.cmdkRoute,b=c.dataset.cmdkAction;if(window.closeCmdk(),v){typeof routeTo=="function"&&routeTo(v);return}if(b){if(b==="open-admin"){window.location.href="/admin/cost";return}if(b.indexOf("lang-")===0){var C=b.slice(5);typeof applyLang=="function"&&applyLang(C)}}}}function p(){var c=document.getElementById("cmdk-mask"),u=document.getElementById("cmdk-input"),v=document.getElementById("cmdk-body");if(!(!c||!u||!v)){c.addEventListener("click",function(E){E.target===c&&window.closeCmdk()});var b=document.getElementById("cmdk-esc-btn");b&&b.addEventListener("click",function(){window.closeCmdk()}),u.addEventListener("input",function(E){i(E.target.value)}),u.addEventListener("keydown",function(E){E.key==="ArrowDown"?(E.preventDefault(),s(1)):E.key==="ArrowUp"?(E.preventDefault(),s(-1)):E.key==="Enter"?(E.preventDefault(),r(c.querySelector(".cmdk-item.focus"))):E.key==="Escape"&&(E.preventDefault(),window.closeCmdk())}),v.addEventListener("click",function(E){var m=E.target.closest(".cmdk-item");m&&r(m)}),v.addEventListener("mousemove",function(E){var m=E.target.closest(".cmdk-item");!m||m.style.display==="none"||m.classList.contains("cmdk-item-locked")||(a().forEach(function(h){h.classList.remove("focus")}),m.classList.add("focus"))});var C=document.getElementById("topbar-search");C&&(C.addEventListener("click",function(){window.openCmdk()}),C.addEventListener("keydown",function(E){(E.key==="Enter"||E.key===" ")&&(E.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(c){if((c.metaKey||c.ctrlKey)&&(c.key==="k"||c.key==="K")){c.preventDefault(),window.openCmdk();return}if(c.key==="Escape"){var u=document.getElementById("cmdk-mask");if(u&&u.classList.contains("show")){window.closeCmdk();return}var v=document.getElementById("avatar-popup");v&&v.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var l=(navigator.userAgent||"").toLowerCase(),d=l.indexOf("mac")>=0||l.indexOf("iphone")>=0||l.indexOf("ipad")>=0;d||document.body.classList.add("is-windows")}catch{}function f(){n(),p(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",f):f()})();(function(){function n(b){return String(b??"").replace(/[&<>"']/g,function(C){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[C]})}function a(b){if(!b||isNaN(b))return"";var C=Number(b);return C<1024?C+" B":C<1024*1024?(C/1024).toFixed(1)+" KB":(C/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(b){var C=b.target.closest&&b.target.closest(".recon-collapse-head");if(C&&!(b.target.closest("button")||b.target.closest("a"))){var E=C.closest(".recon-collapse");if(E){var m=E.getAttribute("data-collapsed")==="true";E.setAttribute("data-collapsed",m?"false":"true"),m&&(E.id==="vex-summary-collapse"&&f(),E.id==="vex-detail-collapse"&&c())}}}),document.addEventListener("keydown",function(b){if(!(b.key!=="Enter"&&b.key!==" ")){var C=b.target.closest&&b.target.closest(".recon-collapse-head");C&&(b.preventDefault(),C.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){l("vat"),l("gl")}function p(b){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(b)||[]}catch{}var C=document.getElementById(b==="vat"?"glv-vat-input":"glv-gl-input");return C&&C.files?Array.from(C.files):[]}function l(b){var C=document.getElementById(b==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(C){var E=p(b),m=b==="vat"?"glv-up-vat-title":"glv-up-gl-title",h=b==="vat"?"① 销项税报告":"② 总账 GL",M=window.t&&window.t(m)||h,B=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),P=n(window.t&&window.t("vex-preview-clear-all")||"全清"),H=o[b]||"",_=E.length;C.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n(M)+' <span class="vex-pp-col-count">'+_+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+b+'" type="text" placeholder="'+B+'" value="'+n(H)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+b+'" type="button">'+P+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+b+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+b+'-pg"></div>';var g=document.getElementById("glv-pp-search-"+b);g&&g.addEventListener("input",function(S){o[b]=S.target.value,d(b)});var k=document.getElementById("glv-pp-clearall-"+b);k&&k.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(b)}),d(b)}}function d(b){var C=document.getElementById("glv-pp-"+b+"-list"),E=document.getElementById("glv-pp-"+b+"-pg");if(C){var m=p(b),h=(o[b]||"").toLowerCase(),M=m.map(function(H,_){return{f:H,i:_}}),B=h?M.filter(function(H){return H.f.name.toLowerCase().indexOf(h)>=0}):M;if(C.innerHTML=B.map(function(H){var _=H.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(_.name)+'">'+n(_.name)+'</span><span class="vex-pp-fi-size">'+a(_.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+b+'" data-idx="'+H.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),C.querySelectorAll(".vex-pp-fi-del").forEach(function(H){H.addEventListener("click",function(){var _=H.dataset.kind,g=parseInt(H.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(_,isNaN(g)?null:g)})}),E){var P=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";E.textContent=P.replace("{n}",B.length).replace("{m}",B.length)}}}function f(){var b=function(E,m){var h=document.getElementById(E);h&&(h.textContent=m==null?"—":String(m))},C=window._vexLastTask||{};b("vex-sum-total",C.total),b("vex-sum-matched",C.matched),b("vex-sum-diff",C.diff),b("vex-sum-incomplete",C.incomplete),b("vex-sum-cash",C.cash),document.getElementById("vex-summary-sub")}function c(){var b=window._vexLastTask&&window._vexLastTask.diff_rows||[],C=document.getElementById("vex-detail-tbody"),E=document.getElementById("vex-detail-table"),m=document.getElementById("vex-detail-empty");if(!(!C||!E||!m)){if(b.length===0){E.style.display="none",m.style.display="";return}m.style.display="none",E.style.display="";var h=b.map(function(B){return'<tr><td class="recon-detail-cell-mono">'+n(B.invoice_no||"")+"</td><td>"+n(B.field||"")+"</td><td>"+n(B.report_value||"")+"</td><td>"+n(B.invoice_value||"")+"</td><td>"+n(B.kind||"")+"</td></tr>"}).join("");C.innerHTML=h;var M=document.getElementById("vex-detail-sub");M&&(M.textContent=String(b.length))}}function u(){var b=document.getElementById("glv-toggle-preview");b&&!b._reconBound&&(b._reconBound=!0,b.addEventListener("click",function(){var C=document.getElementById("glv-preview-panel"),E=document.getElementById("glv-toggle-preview-label"),m=C&&C.style.display!=="none";C&&(C.style.display=m?"none":""),b.classList.toggle("open",!m),E&&(E.textContent=m?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),m||r()})),["glv-vat-input","glv-gl-input"].forEach(function(C){var E=document.getElementById(C);!E||E._reconWatched||(E._reconWatched=!0,E.addEventListener("change",function(){var m=document.getElementById("glv-preview-panel");m&&m.style.display!=="none"&&r()}))})}function v(){var b=document.getElementById("vex-summary-collapse"),C=document.getElementById("vex-detail-collapse");b&&(b.style.display=""),C&&(C.style.display=""),f(),c()}window._fillVexSummary=f,window._fillVexDetail=c,window._onVexResultShown=v,document.addEventListener("DOMContentLoaded",function(){u()}),setTimeout(u,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var b=document.getElementById("glv-preview-panel");b&&b.style.display!=="none"&&r();var C=document.getElementById("glv-toggle-preview-label"),E=document.getElementById("glv-toggle-preview");C&&E&&(C.textContent=E.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:f,fillVexDetail:c}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(p=>{p.addEventListener("click",()=>{i.forEach(u=>u.classList.remove("active")),p.classList.add("active");const l=p.dataset.reconTab,d=document.getElementById("recon-pane-bank"),f=document.getElementById("recon-pane-sale-vat"),c=document.getElementById("recon-pane-gl-vat");d&&(d.style.display=l==="bank"?"":"none"),f&&(f.style.display=l==="sale-vat"?"":"none"),c&&(c.style.display=l==="gl-vat"?"":"none"),l==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),l==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const p=document.createElement("button");return p.id="settings-modal-close",p.className="settings-modal-close",p.setAttribute("aria-label","close"),p.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(p,i.firstChild),p.addEventListener("click",s),r.addEventListener("click",l=>{l.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(l){console.warn("renderSettings:",l)}let p=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');p&&p.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=U=>document.getElementById(U);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(U){return String(U??"").replace(/[&<>"']/g,Q=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Q])}function r(U){return U<1024?U+" B":U<1024*1024?(U/1024).toFixed(1)+" KB":(U/1024/1024).toFixed(1)+" MB"}let p=[],l=[],d=!1,f=[],c=50,u=50,v="",b="";async function C(){try{const U=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!U.ok)return;const ee=(await U.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,oe])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=oe??0)})}catch{}}async function E(){try{const U=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!U.ok)return;const Q=await U.json();B(Q.rows||[])}catch{}}const m=10;var h=1;function M(){var U=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(h=1,B(f),!!U){var Q=document.getElementById("vex-task-tbody");Q&&Q.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(U)>=0?"":"none")})}}function B(U){f=U||f;const Q=document.getElementById("vex-task-tbody");if(!Q)return;if(!f.length){Q.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",P(0);return}const ee=Math.ceil(f.length/m);h>ee&&(h=ee);const ne=(h-1)*m;H(f.slice(ne,ne+m)),P(f.length)}function P(U){const Q=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),oe=document.getElementById("vex-task-next");if(!Q)return;if(U<=m){Q.style.display="none";return}Q.style.display="";const ue=Math.ceil(U/m);ee&&(ee.textContent=h+" / "+ue),ne&&(ne.disabled=h<=1),oe&&(oe.disabled=h>=ue)}function H(U){const Q=document.getElementById("vex-task-tbody");if(!Q)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Q.innerHTML=U.map(x=>{const $=x.created_at?new Date(x.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",j=x.period||"—",G=x.matched_count!=null?x.matched_count+" ✓ · "+x.mismatched_count+" ⚠":"—",N=x.mismatch_amount!=null?"฿ "+Number(x.mismatch_amount).toLocaleString():"—",y=x.elapsed_seconds!=null?x.elapsed_seconds.toFixed(1)+" s":"—",F=x.status||"pending",O=x.client_name&&x.client_name!=="client"?x.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(x.id)}" style="cursor:pointer">
                <td>${$}</td>
                <td>${i(O)}</td>
                <td>${i(j)}</td>
                <td>${(x.invoice_count||0)+" / "+(x.report_count||0)}</td>
                <td>${G}</td>
                <td>${N}</td>
                <td><span class="badge ${ne[F]||"badge-gray"}">${ee[F]||F}</span></td>
                <td>${y}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(x.id)}" title="${t("hist_export")||"导出"}">${oe}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(x.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Q.querySelectorAll(".vex-task-dl-btn").forEach(x=>{x.addEventListener("click",async $=>{$.stopPropagation();const j=x.dataset.taskId;try{const G=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(j)+"/download",{credentials:"include",headers:s()});if(G.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!G.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const N=await G.blob(),F=(G.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),O=F?decodeURIComponent(F[1]):"vat_recon_"+j+".xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=O,X.click(),setTimeout(()=>URL.revokeObjectURL(J),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Q.querySelectorAll(".vex-task-del-btn").forEach(x=>{x.addEventListener("click",$=>{$.stopPropagation(),g(x.dataset.taskId)})}),M()}function _(){var U=document.getElementById("vex-task-prev"),Q=document.getElementById("vex-task-next");U&&!U._vexBound&&(U._vexBound=!0,U.addEventListener("click",function(){h>1&&(h--,B())})),Q&&!Q._vexBound&&(Q._vexBound=!0,Q.addEventListener("click",function(){var ee=Math.ceil(f.length/m);h<ee&&(h++,B())}))}async function g(U){const Q=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Q,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(U),{method:"DELETE",credentials:"include",headers:s()});if(!oe.ok)throw new Error(oe.status);showToast(t("vex-task-delete-ok")||"已删除","success"),E(),C()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function k(U){const Q=window._currentLang||"th",ee={zh:`已忽略 ${U} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${U} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${U} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${U} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Q]||ee.th,"warn")}function S(U){const Q=new Set(p.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of U){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),p.push(ne),p.length>=1e3))break}ee>0&&k(ee),p.length>1e3&&(p=p.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),D()}function T(U){const Q=new Set(l.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of U){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),l.push(ne),l.length>=30))break}ee>0&&k(ee),l.length>30&&(l=l.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),D()}function q(U){p.splice(U,1),D()}function L(U){l.splice(U,1),D()}function D(){const U=o("vex-list-invoice"),Q=o("vex-list-report"),ee=o("vex-count-invoice"),ne=o("vex-count-report");ee&&(ee.textContent=p.length),ne&&(ne.textContent=l.length);const oe=($,j,G)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i($.name)}">${i($.name)}</span>
            <span class="vex-fi-s">${r($.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${G}" data-vex-idx="${j}" aria-label="remove">×</button>
        </div>`;U&&(U.innerHTML=p.map(($,j)=>oe($,j,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Q&&(Q.innerHTML=l.map(($,j)=>oe($,j,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach($=>{$.addEventListener("click",j=>{const G=$.dataset.vexKind,N=parseInt($.dataset.vexIdx,10);G==="inv"?q(N):L(N)})});const ue=p.length>0&&l.length>0;o("vex-build").disabled=!ue||d;const x=o("vex-action-info");x&&(!p.length||!l.length?(x.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",x.className="vex-action-info muted"):(x.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",p.length).replace("{b}",l.length),x.className="vex-action-info ok")),te()}const Y='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',V='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',W='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const U=o("vex-preview-panel");if(!U||U.style.display==="none")return;re("inv"),re("rep");const Q=o("vex-pp-guide");Q&&(Q.style.display=p.length>100?"flex":"none")}function re(U){const Q=o(U==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Q)return;const ee=U==="inv"?p:l,ne=U==="inv"?v:b,oe=t(U==="inv"?"vex-preview-invoice":"vex-preview-report")||(U==="inv"?"销售发票":"VAT 报告"),ue=i(t("vex-preview-search")||"搜索文件名..."),x=i(t("vex-preview-clear-all")||"全清");Q.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(oe)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${U}" type="text"
                       placeholder="${ue}" value="${i(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${U}" type="button">${x}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${U}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${U}-pg"></div>`;const $=o("vex-pp-search-"+U);$&&$.addEventListener("input",G=>{U==="inv"?(v=G.target.value,c=50):(b=G.target.value,u=50),A(U)});const j=o("vex-pp-clearall-"+U);j&&j.addEventListener("click",()=>{U==="inv"?(p=[],v="",c=50):(l=[],b="",u=50),D()}),A(U)}function A(U){const Q=o("vex-pp-"+U+"-list"),ee=o("vex-pp-"+U+"-pg");if(!Q)return;const ne=U==="inv"?p:l,oe=U==="inv"?v:b,ue=U==="inv"?c:u,x=U==="inv"?Y:V,$=ne.map((N,y)=>({f:N,i:y})),j=oe?$.filter(({f:N})=>N.name.toLowerCase().includes(oe.toLowerCase())):$,G=j.slice(0,ue);if(Q.innerHTML=G.map(({f:N,i:y})=>`
            <div class="vex-pp-file-row">
                ${x}
                <span class="vex-pp-fi-name" title="${i(N.name)}">${i(N.name)}</span>
                <span class="vex-pp-fi-size">${r(N.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${U}" data-ridx="${y}" aria-label="remove">${W}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${U}" style="height:1px;flex-shrink:0"></div>`,Q.querySelectorAll(".vex-pp-fi-del").forEach(N=>{N.addEventListener("click",()=>{const y=parseInt(N.dataset.ridx,10);N.dataset.kind==="inv"?q(y):L(y)})}),ee){const N=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=N.replace("{n}",G.length).replace("{m}",j.length)}I(U,j.length)}function I(U,Q){if((U==="inv"?c:u)>=Q)return;const ne=o("vex-pp-sentinel-"+U),oe=o("vex-pp-"+U+"-list");if(!ne||!oe)return;const ue=new IntersectionObserver(x=>{x[0].isIntersecting&&(ue.disconnect(),U==="inv"?c+=50:u+=50,A(U))},{root:oe,threshold:.8});ue.observe(ne)}function w(U,Q,ee,ne){const oe=o(U),ue=o(Q);!oe||!ue||(oe.addEventListener("click",()=>ue.click()),oe.addEventListener("keydown",x=>{(x.key==="Enter"||x.key===" ")&&(x.preventDefault(),ue.click())}),oe.addEventListener("dragover",x=>{x.preventDefault(),oe.classList.add("drag-over")}),oe.addEventListener("dragleave",()=>oe.classList.remove("drag-over")),oe.addEventListener("drop",x=>{x.preventDefault(),oe.classList.remove("drag-over");const j=Array.from(x.dataTransfer.files).filter(G=>a.test(G.name));if(!j.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(j)}),ue.addEventListener("change",()=>{const x=Array.from(ue.files);ee(x),ue.value=""}))}async function R(){if(d||!p.length||!l.length)return;d=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var U=document.getElementById("vex-download");U&&(U.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(oe){var ue=document.getElementById(oe);ue&&(ue.style.display="none")});const Q=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",p.length).replace("{b}",l.length);const ee=setInterval(()=>{const oe=Math.floor((Date.now()-Q)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",oe).replace("{a}",p.length).replace("{b}",l.length)},1e3);try{const oe=new FormData;for(const pe of p)oe.append("invoices",pe);for(const pe of l)oe.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";oe.append("lang",ue);const x=localStorage.getItem("mrpilot_token")||"",$=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:oe});let j=null;try{j=await $.json()}catch{j=null}if(!$.ok||!j||!j.ok||!j.job_id)throw clearInterval(ee),new Error(j&&j.detail||"HTTP "+$.status);const G=o("vex-progress-sub"),N=await window._reconPollJob(j.job_id,x,{onProgress:pe=>{G&&(G.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!N||N.status!=="done"||!N.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const y=N.result_id;let F=0;const O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(y)+"/download",{headers:s()});if(!O.ok)throw new Error("HTTP "+O.status);const X=(O.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",se=await O.blob(),ce=URL.createObjectURL(se),ae=o("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),y&&(F=await Z(y)),window._onVexResultShown&&window._onVexResultShown(),F>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",F),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),C(),setTimeout(E,800)}catch(oe){clearInterval(ee),o("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(oe.message||oe);showToast(ue,"error")}finally{d=!1,o("vex-build").disabled=!1}}function z(){p=[],l=[];var U=document.getElementById("vex-download");U&&(U.style.display="none"),D()}function K(U){if(U==null)return"—";var Q=parseFloat(U);return isNaN(Q)?"—":Q.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(U){try{var Q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(U),{headers:s()});if(!Q.ok)throw new Error(Q.status);var ee=await Q.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var oe=ne.rows||[],ue=[];oe.forEach(function(j){j.kind==="invoice_orphan"?ue.push({invoice_no:j.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:K(j.amount_inv),kind:j.kind}):j.kind==="report_orphan"?ue.push({invoice_no:j.invoice_no||"",field:"仅报告有",report_value:K(j.amount_rep),invoice_value:"—",kind:j.kind}):j.dims&&Object.keys(j.dims).length>0&&Object.keys(j.dims).forEach(function(G){var N=String(j.dims[G]||""),y=N.split(" ≠ ");ue.push({invoice_no:j.invoice_no||"",field:G,report_value:y[0]||N,invoice_value:y.length>1?y[1]:"—",kind:"diff"})})});var x=oe.filter(function(j){return j.kind==="matched_cash"}).length,$=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:$,cash:x,diff_rows:ue,task_id:U},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),$}catch{return 0}}function le(){const U=document.getElementById("vex-pane");U&&U.querySelectorAll("[data-i18n]").forEach(Q=>{const ee=t(Q.dataset.i18n);ee&&(Q.textContent=ee)}),D(),E()}function ie(){w("vex-drop-invoice","vex-input-invoice",S),w("vex-drop-report","vex-input-report",T);const U=o("vex-build"),Q=o("vex-reset");U&&U.addEventListener("click",R),Q&&Q.addEventListener("click",z),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(oe=>{oe.addEventListener("click",()=>{C(),E()})}),_();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",M);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const oe=o("vex-preview-panel"),ue=o("vex-toggle-preview-label"),x=oe&&oe.style.display!=="none";oe&&(oe.style.display=x?"none":""),ne&&ne.classList.toggle("open",!x),ue&&(ue.textContent=x?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),x||te()}),D(),C()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=I=>document.getElementById(I),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},i={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},r=I=>(i[a()]||i.th)[I]||I;function p(I){const w=a(),z={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[I];return z?z[w]||z.th||z.en:r("error")||"Error"}const l=I=>I==null||isNaN(I)?"":Number(I).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function d(I,w,R,z){const K=e(I),Z=e(w),le=e(R);if(!K||!Z||!le)return;const ie=U=>{if(!U||!U.length)return;const Q=Array.isArray(s[z])?s[z].slice():[],ee=new Set(Q.map(ne=>ne.name+"|"+ne.size));for(const ne of U){if(!ne)continue;const oe=ne.name+"|"+ne.size;ee.has(oe)||(Q.push(ne),ee.add(oe))}s[z]=Q,f(le,Q),u(),v(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};K.addEventListener("click",()=>Z.click()),K.addEventListener("keydown",U=>{(U.key==="Enter"||U.key===" ")&&(U.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{ie(Array.from(Z.files||[])),Z.value=""}),K.addEventListener("dragover",U=>{U.preventDefault(),K.classList.add("drag-over")}),K.addEventListener("dragleave",()=>K.classList.remove("drag-over")),K.addEventListener("drop",U=>{U.preventDefault(),K.classList.remove("drag-over");const Q=U.dataTransfer&&U.dataTransfer.files?Array.from(U.dataTransfer.files):[];ie(Q)})}function f(I,w){if(!I)return;if(!w||w.length===0){I.textContent="";return}const R=w.reduce((z,K)=>z+Math.round(K.size/1024),0);if(w.length===1)I.textContent=w[0].name+"  ("+R+" KB)";else{const z=window.t&&window.t("glv-files-count")||"{n} 个文件";I.textContent=z.replace("{n}",w.length)+"  ("+R+" KB)"}}function c(I){const w=s[I];return Array.isArray(w)?w:w?[w]:[]}function u(){const I=e("btn-glv-run");if(!I)return;const w=c("glFile").length>0&&c("vatFile").length>0;I.disabled=!w||s.running}function v(){const I=e("glv-status");if(!I||s.running)return;const w=c("vatFile").length,R=c("glFile").length;w===0&&R===0?(I.className="vex-action-info muted",I.innerHTML="<span>"+r("hint_need_both")+"</span>"):w>0&&R>0?(I.className="vex-action-info ok",I.innerHTML="<span>"+r("hint_ready")+"</span>"):(I.className="vex-action-info muted",I.innerHTML="<span>"+r("hint_need_one_more")+"</span>")}function b(I,w){const R=I==="vat"?"vatFile":"glFile",z=I==="vat"?"glv-vat-input":"glv-gl-input",K=I==="vat"?"glv-vat-name":"glv-gl-name",Z=c(R);w==null?s[R]=[]:s[R]=Z.filter((ie,U)=>U!==w);const le=e(z);le&&(le.value=""),f(e(K),c(R)),u(),v(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=b;function C(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const I=e("glv-vat-input");I&&(I.value="");const w=e("glv-gl-input");w&&(w.value="");const R=e("glv-vat-name");R&&(R.textContent="");const z=e("glv-gl-name");z&&(z.textContent="");const K=e("glv-result");K&&(K.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),u(),v(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function E(I){const w=e("glv-tbody");if(!w)return;re(I.length),w.innerHTML="";const R=r("not_found"),z=document.createDocumentFragment();I.forEach(K=>{const Z=document.createElement("tr"),le=(ne,oe)=>{const ue=document.createElement("td");return oe&&(ue.className=oe),ue.textContent=ne,ue},ie=K.gl_amount===null||K.gl_amount===void 0,U=K.diff;let Q="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Q+=" glv-cell-missing"):Math.abs(U||0)<.005?Q+=" glv-cell-ok":Q+=" glv-cell-diff",Z.appendChild(le(K.doc_no||"","glv-doc")),Z.appendChild(le(K.date||"","")),Z.appendChild(le(K.customer_name||"","")),Z.appendChild(le(l(K.vat_amount),"glv-num")),Z.appendChild(le(ie?R:l(K.gl_amount),ee)),Z.appendChild(le(ie?R:l(K.diff),Q)),Z.appendChild(le(K.account_codes||"","glv-doc")),z.appendChild(Z)}),w.appendChild(z)}function m(I){const w=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!w)return;w.innerHTML="",[{label:r("s_gl_total"),amount:I.gl_total,emph:!0,items:[],negate:!1},{label:r("s_minus_gl_cr"),amount:-(I.gl_only_credit||0),emph:!1,items:I.gl_only_credit_items||[],negate:!0},{label:r("s_plus_gl_dr"),amount:I.gl_only_debit||0,emph:!1,items:I.gl_only_debit_items||[],negate:!1},{label:r("s_plus_vat_p"),amount:I.vat_only_positive||0,emph:!1,items:I.vat_only_positive_items||[],negate:!1},{label:r("s_minus_vat_n"),amount:I.vat_only_negative||0,emph:!1,items:I.vat_only_negative_items||[],negate:!1},{label:r("s_vat_total"),amount:I.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:z,amount:K,emph:Z,items:le,negate:ie})=>{const U=document.createElement("tr");U.className=Z?"glv-summary-total":"glv-summary-sect";const Q=document.createElement("td"),ee=document.createElement("td");Q.textContent=z,ee.textContent=Z?l(K):"",U.appendChild(Q),U.appendChild(ee),w.appendChild(U),(le||[]).forEach(ne=>{const oe=document.createElement("tr");oe.className="glv-summary-item";const ue=document.createElement("td"),x=document.createElement("td"),$=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+$.join("  ·  ");const j=ie?-(ne.amount||0):ne.amount||0;x.textContent=l(j),oe.appendChild(ue),oe.appendChild(x),w.appendChild(oe)})})}function h(I){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=I&&I.matched!=null?I.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=I&&I.diff!=null?I.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=I&&I.unmatched!=null?I.unmatched:"—")}function M(I){if(!I)return"";try{const w=new Date(I);if(isNaN(w.getTime()))return I;const R=z=>String(z).padStart(2,"0");return w.getFullYear()+"-"+R(w.getMonth()+1)+"-"+R(w.getDate())+" "+R(w.getHours())+":"+R(w.getMinutes())}catch{return I}}const B=10;var P=[],H=1;function _(){H=1,g();var I=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(I){var w=e("glv-history-tbody");w&&w.querySelectorAll("tr").forEach(function(R){R.dataset.taskId&&(R.style.display=R.textContent.toLowerCase().indexOf(I)>=0?"":"none")})}}function g(){const I=e("glv-history-table-wrap"),w=e("glv-history-empty"),R=e("glv-history-tbody"),z=e("glv-history-pager"),K=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!R)return;if(R.innerHTML="",!P.length){I&&(I.style.display="none"),w&&(w.style.display=""),z&&(z.style.display="none");return}I&&(I.style.display=""),w&&(w.style.display="none");const ie=Math.ceil(P.length/B);H>ie&&(H=ie);const U=(H-1)*B,Q=P.slice(U,U+B);z&&(z.style.display=P.length>B?"":"none",K&&(K.textContent=H+" / "+ie),Z&&(Z.disabled=H<=1),le&&(le.disabled=H>=ie)),Q.forEach(ne=>{const oe=document.createElement("tr");oe.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=M(ne.created_at);const x=document.createElement("td");x.className="glv-history-file",x.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),x.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const $=document.createElement("td");$.className="glv-num",$.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const j=document.createElement("td");j.className="glv-num",j.textContent=ne.matched_count||0;const G=document.createElement("td");G.className="glv-num",G.textContent=ne.diff_count||0;const N=document.createElement("td");N.className="glv-num",N.textContent=ne.unmatched_count||0;const y=document.createElement("td");y.className="glv-history-actions";const F=(de,se,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=se,pe.setAttribute("aria-label",se),pe.innerHTML=de,pe.onclick=ae,pe},O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';y.appendChild(F(O,r("hist_load"),"",()=>T(ne.id))),y.appendChild(F(J,r("hist_export"),"",()=>q(ne.id))),y.appendChild(F(X,r("hist_delete"),"glv-del",()=>L(ne.id))),[ue,x,$,j,G,N,y].forEach(de=>oe.appendChild(de)),R.appendChild(oe)})}function k(){var I=e("glv-history-prev"),w=e("glv-history-next");I&&!I._glvBound&&(I._glvBound=!0,I.addEventListener("click",function(){H>1&&(H--,g())})),w&&!w._glvBound&&(w._glvBound=!0,w.addEventListener("click",function(){var R=Math.ceil(P.length/B);H<R&&(H++,g())}))}async function S(){try{const w=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();P=w&&w.tasks||[],H=1,g(),k()}catch(I){console.error("[gl-vat] history load failed:",I)}}async function T(I){try{const R=await(await fetch("/api/recon/gl-vat/"+I,{headers:o()})).json();if(!R||!R.ok)throw new Error("load_failed");s.currentTaskId=I,s.lastDetail=R.detail||[],s.lastSummary=R.summary||{},h(R.stats||{}),E(s.lastDetail),m(s.lastSummary);const z=e("glv-result");z&&(z.style.display=""),W(),window.scrollTo({top:z?z.offsetTop-80:0,behavior:"smooth"})}catch(w){console.error("[gl-vat] load task failed:",w),alert(r("error")+": "+(w.message||w))}}async function q(I){try{const w="/api/recon/gl-vat/"+I+"/export?lang="+encodeURIComponent(a()),R=await fetch(w,{headers:o()});if(!R.ok)throw new Error("HTTP "+R.status);const z=await R.blob(),K=document.createElement("a");K.href=URL.createObjectURL(z),K.download="GL_VAT_recon_"+I+".xlsx",document.body.appendChild(K),K.click(),setTimeout(()=>{URL.revokeObjectURL(K.href),K.remove()},200)}catch(w){console.error("[gl-vat] exportTask failed:",w),typeof showToast=="function"&&showToast(r("error")+": "+(w.message||w),"error")}}async function L(I){let w;if(typeof window.showConfirm=="function"?w=await window.showConfirm(r("confirm_delete"),{danger:!0}):w=confirm(r("confirm_delete")),!!w)try{const R=await fetch("/api/recon/gl-vat/"+I,{method:"DELETE",headers:o()});if(!R.ok)throw new Error("HTTP "+R.status);S()}catch(R){console.error("[gl-vat] delete failed:",R),typeof showToast=="function"&&showToast(r("error")+": "+(R.message||R),"error")}}async function D(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(r("need_files"),"warn");return}s.running=!0,u();const I=e("glv-status"),w=e("glv-progress"),R=e("glv-progress-sub");I&&(I.className="vex-action-info muted",I.style.color="",I.innerHTML="<span>"+r("running")+"</span>"),w&&(w.style.display=""),R&&(R.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const z=new FormData,K=c("vatFile"),Z=c("glFile");for(const ie of K)z.append("vat_files",ie,ie.name);for(const ie of Z)z.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";z.append("revenue_prefix",le),z.append("lang",a());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:z});let U=null;try{U=await ie.json()}catch{U=null}if(!ie.ok||!U||!U.ok||!U.job_id)throw new Error(U&&U.detail||U&&U.error||"HTTP "+ie.status);const Q=e("glv-progress-sub"),ee=await window._reconPollJob(U.job_id,n(),{onProgress:x=>{Q&&(Q.textContent=window._reconProgressText(x,a()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(p(ee.error_code)):new Error(r("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:o()});let oe=null;try{oe=await ne.json()}catch{oe=null}if(!ne.ok||!oe||!oe.ok)throw new Error(oe&&oe.detail||oe&&oe.error||"HTTP "+ne.status);s.currentTaskId=oe.task_id,s.lastDetail=oe.detail||[],s.lastSummary=oe.summary||{},h(oe.stats||{}),E(s.lastDetail),m(s.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),W(),I&&(I.className="vex-action-info ok",I.style.color="",I.innerHTML="<span>"+r("done")+" · GL "+(oe.gl_row_count||0)+" · VAT "+(oe.vat_row_count||0)+"</span>"),S()}catch(ie){console.error("[gl-vat] run failed:",ie),I&&(I.className="vex-action-info",I.style.color="#ef4444",I.innerHTML="<span>"+r("error")+": "+(ie.message||ie)+"</span>")}finally{s.running=!1,w&&(w.style.display="none"),u()}}async function Y(){if(s.currentTaskId)try{const I="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),w=await fetch(I,{headers:o()});if(!w.ok)throw new Error("HTTP "+w.status);const R=await w.blob(),z=document.createElement("a");z.href=URL.createObjectURL(R),z.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(z),z.click(),setTimeout(()=>{URL.revokeObjectURL(z.href),z.remove()},200)}catch(I){console.error("[gl-vat] export failed:",I),typeof showToast=="function"&&showToast(r("error")+": "+(I.message||I),"error")}}function V(){s.running||v(),S(),s.lastDetail&&s.lastDetail.length&&E(s.lastDetail),s.lastSummary&&m(s.lastSummary)}function W(){var I=e("glv-kpi-strip");I&&(I.style.display="");var w=e("glv-section-summary");w&&w.setAttribute("data-collapsed","false");var R=e("glv-section-detail");R&&R.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(I=>{const w=I.getAttribute("data-toggle"),R=document.getElementById(w);if(!R)return;const z=K=>{if(K.target&&K.target.closest("button")!==null&&!K.target.classList.contains("glv-section-head"))return;const Z=R.getAttribute("data-collapsed")==="true";R.setAttribute("data-collapsed",Z?"false":"true")};I.addEventListener("click",z),I.addEventListener("keydown",K=>{(K.key==="Enter"||K.key===" ")&&(K.preventDefault(),z(K))})})}function re(I){const w=e("glv-detail-count");w&&(w.textContent=I!=null?String(I):"")}function A(){if(s.inited){S();return}s.inited=!0,d("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),d("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const I=e("btn-glv-run");I&&I.addEventListener("click",D);const w=e("btn-glv-export");w&&w.addEventListener("click",Y);const R=e("btn-glv-reset");R&&R.addEventListener("click",C);const z=e("glv-hist-search");z&&z.addEventListener("input",_),te(),h(null),v(),window._loadGlvHistory=S,S(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",V)}window.GlVatRecon={ensureInit:A},window._glvPreviewFiles=function(I){return c(I==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let i={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const T=typeof _userInfo<"u"?_userInfo:null;return!!(T&&(T.role==="owner"||T.is_super_admin))}function p(){const T=typeof _userInfo<"u"?_userInfo:null;return!!(T&&T.id===s)}function l(T){return typeof escapeHtml=="function"?escapeHtml(T==null?"":String(T)):String(T??"")}function d(T,q){try{typeof showToast=="function"&&showToast(T,q||"info")}catch{}}async function f(T,q){const L=localStorage.getItem("mrpilot_token");if(L&&!(i.loaded[T]&&!q))try{const D=await fetch("/api/erp/mappings/"+T,{headers:{Authorization:"Bearer "+L}});if(!D.ok)throw new Error("http_"+D.status);const Y=await D.json();i.items[T]=Y.items||[],i.loaded[T]=!0}catch{i.items[T]=[],i.loaded[T]=!1}}async function c(T){if(i.clientLoaded)return;const q=localStorage.getItem("mrpilot_token");if(q)try{const L=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+q}});if(!L.ok)throw new Error("http_"+L.status);const D=await L.json();i.clientList=(D.clients||D.items||[]).filter(Y=>Y.is_active!==!1),i.clientLoaded=!0}catch{i.clientList=[]}}function u(){const T=document.getElementById("erp-map-pane-wrap");if(!T)return;const q=!r();let L="";q&&(L+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+l(t("erp-map-readonly-tip"))+"</div>"),L+='<div class="erp-map-toolbar">',!q&&i.sub!=="products"&&(L+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+l(t("erp-map-add-row"))+"</button>"),L+="</div>",L+='<div class="erp-map-table" id="erp-map-table-host"></div>',T.innerHTML=L,v();const D=document.getElementById("erp-map-dev-bar");D&&(D.style.display=r()&&p()?"":"none")}function v(){const T=document.getElementById("erp-map-table-host");if(!T)return;const q=i.sub,L=i.items[q]||[],D=i.addingNew[q],Y=!r();if(!L.length&&!D){T.innerHTML='<div class="erp-map-empty"><strong>'+l(t("erp-map-empty-"+q))+"</strong>"+l(t("erp-map-empty-"+q+"-sub"))+"</div>";return}let V="";V+=b(q),D&&!Y&&(V+=M(q)),L.forEach(function(W){V+=B(q,W,Y)}),T.innerHTML=V}function b(T){return T==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+l(t("erp-map-col-client"))+"</div><div>"+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":T==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-category"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":T==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+l(t("erp-map-col-item-name"))+"</div><div>"+l(t("erp-map-col-erp-product-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-tax"))+"</div><div>"+l(t("erp-map-col-erp-tax-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>"}function C(T,q){let L='<select class="form-input" data-erp-field="'+q+'">';return L+='<option value="">'+l(t("erp-map-pick-erp"))+"</option>",e.forEach(function(D){const Y=D===T?" selected":"";L+='<option value="'+D+'"'+Y+">"+l(n[D])+"</option>"}),L+="</select>",L}function E(T){let q='<select class="form-input" data-erp-field="client_id">';return q+='<option value="">'+l(t("erp-map-pick-client"))+"</option>",(i.clientList||[]).forEach(function(L){const D=String(L.id)===String(T)?" selected":"";q+='<option value="'+L.id+'"'+D+">"+l(L.name||"#"+L.id)+"</option>"}),q+="</select>",q}function m(T){let q='<select class="form-input" data-erp-field="pearnly_category">';return q+='<option value="">'+l(t("erp-map-pick-cat"))+"</option>",a.forEach(function(L){const D=L===T?" selected":"";q+='<option value="'+L+'"'+D+">"+l(t("erp-map-cat-"+L))+"</option>"}),q+="</select>",q}function h(T){let q='<select class="form-input" data-erp-field="pearnly_tax_kind">';return q+='<option value="">'+l(t("erp-map-pick-tax"))+"</option>",o.forEach(function(L){const D=L===T?" selected":"";q+='<option value="'+L+'"'+D+">"+l(t("erp-map-tax-"+L))+"</option>"}),q+="</select>",q}function M(T){const q='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+l(t("erp-map-save"))+"</button>";return T==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+l(t("erp-map-col-client"))+'">'+E("")+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+C("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+q+"</div></div>":T==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+C("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-category"))+'">'+m("")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+l(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+l(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+q+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+C("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-tax"))+'">'+h("")+'</div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+q+"</div></div>"}function B(T,q,L){const D=L?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+l(q.id)+'" title="'+l(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',Y='<span class="erp-map-erp-badge">'+l(n[q.erp_type]||q.erp_type)+"</span>";if(T==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+l(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+l(q.client_name||"#"+q.client_id)+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(q.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(q.notes||"")+"</div><div>"+D+"</div></div>";if(T==="accounts"){const W=t("erp-map-cat-"+(q.pearnly_category||"other"))||q.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+l(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+l(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+l(W)+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(q.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(q.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(q.notes||"")+"</div><div>"+D+"</div></div>"}if(T==="products")return'<div class="erp-map-row row-products"><div data-label="'+l(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+l(q.item_name||"")+'</div><div data-label="'+l(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+l(q.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(q.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(q.notes||"")+"</div><div>"+D+"</div></div>";const V=t("erp-map-tax-"+(q.pearnly_tax_kind||""))||q.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+l(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+l(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+l(V)+'</span></div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+l(q.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(q.notes||"")+"</div><div>"+D+"</div></div>"}async function P(T){const q=i.sub,L={};T.querySelectorAll("[data-erp-field]").forEach(function(W){L[W.dataset.erpField]=(W.value||"").trim()});const D=localStorage.getItem("mrpilot_token");if(!D)return;let Y={},V="/api/erp/mappings/"+q;if(q==="clients"){if(!L.client_id||!L.erp_type||!L.erp_code){d(t("erp-map-save-fail"),"error");return}Y={client_id:parseInt(L.client_id,10),erp_type:L.erp_type,erp_code:L.erp_code,notes:L.notes||""}}else if(q==="accounts"){if(!L.erp_type||!L.pearnly_category||!L.erp_code){d(t("erp-map-save-fail"),"error");return}Y={erp_type:L.erp_type,pearnly_category:L.pearnly_category,erp_code:L.erp_code,erp_name:L.erp_name||"",notes:L.notes||""}}else{if(!L.erp_type||!L.pearnly_tax_kind||!L.erp_code){d(t("erp-map-save-fail"),"error");return}Y={erp_type:L.erp_type,pearnly_tax_kind:L.pearnly_tax_kind,erp_code:L.erp_code,notes:L.notes||""}}try{const W=await fetch(V,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+D},body:JSON.stringify(Y)});if(!W.ok)throw new Error("http_"+W.status);i.addingNew[q]=!1,await f(q,!0),v(),d(t("erp-map-saved-toast"),"success")}catch{d(t("erp-map-save-fail"),"error")}}async function H(T){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const L=i.sub,D=localStorage.getItem("mrpilot_token");try{const Y=await fetch("/api/erp/mappings/"+L+"/"+encodeURIComponent(T),{method:"DELETE",headers:{Authorization:"Bearer "+D}});if(!Y.ok)throw new Error("http_"+Y.status);await f(L,!0),v(),d(t("erp-map-deleted-toast"),"success")}catch{d(t("erp-map-delete-fail"),"error")}}async function _(){await c(),await f(i.sub,!1),u()}function g(T){T!==i.sub&&(i.sub=T,i.addingNew[T]=!1,["clients","accounts","taxes","products"].forEach(function(q){q!==T&&(i.addingNew[q]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(q){q.classList.toggle("active",q.dataset.erpSubtab===T)}),f(T,!1).then(function(){u()}))}function k(){i.bound||(i.bound=!0,document.addEventListener("click",function(T){const q=T.target.closest(".erp-subtab[data-erp-subtab]");if(q){T.preventDefault();const W=q.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===W)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===W)}),W==="mappings"&&setTimeout(_,50);return}const L=T.target.closest(".erp-map-subtab[data-erp-subtab]");if(L){T.preventDefault(),g(L.dataset.erpSubtab);return}if(T.target.closest("#erp-map-add-btn")){if(T.preventDefault(),!r())return;i.addingNew[i.sub]=!0,v();return}const Y=T.target.closest('[data-erp-save="new"]');if(Y){T.preventDefault();const W=Y.closest('[data-erp-row="new"]');W&&P(W);return}const V=T.target.closest("[data-erp-del]");if(V){T.preventDefault(),H(V.dataset.erpDel);return}}))}function S(){const T=document.getElementById("erp-map-pane-wrap");T&&T.children.length>0&&u(),document.querySelectorAll(".erp-map-subtab").forEach(function(q){const L="erp-map-subtab-"+q.dataset.erpSubtab,D=t(L);D&&D!==L&&(q.textContent=D)})}k(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",S)})();(function(){let e=null,n=0,a=!1;function o(_){return typeof escapeHtml=="function"?escapeHtml(_==null?"":String(_)):String(_??"")}function s(_,g){try{typeof showToast=="function"&&showToast(_,g||"info")}catch{}}async function i(_){const g=Date.now();if(e&&g-n<3e4)return e;const k=localStorage.getItem("mrpilot_token");if(!k)return[];try{const S=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+k}});if(!S.ok)return[];const T=await S.json();return e=T&&T.connectors||[],n=g,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function p(_){try{localStorage.setItem("pn_push_default_connector",_||"")}catch{}}function l(_){if(!_||!_.length)return null;const g=r();if(g){const S=_.find(T=>T.id===g);if(S)return S}const k=_.find(S=>S.is_default);return k||_[0]}function d(_){if(!_)return!1;const g=String(_.status||"").toLowerCase();return g==="exception"||g==="exception_pending"||g==="rejected"}function f(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function c(_){const g=_&&(_.type||_.id);return g==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':g==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function u(_,g){if(!_||!g)return!1;const k=document.getElementById("btn-push-default");k&&(k.disabled=!0,k.classList.add("loading"));const S=localStorage.getItem("mrpilot_token");try{let T,q={method:"POST",headers:{Authorization:"Bearer "+S}};_.type==="xero"?T="/api/erp/xero/push/"+encodeURIComponent(g):(T="/api/erp/push",q.headers["Content-Type"]="application/json",q.body=JSON.stringify({history_id:g,endpoint_id:_.endpoint_id||void 0}));const L=await fetch(T,q);let D={};try{D=await L.json()}catch{}if(!L.ok){let Y=D&&D.detail||"unknown";typeof Y=="object"&&(Y=Y.code||JSON.stringify(Y));let V=String(Y||"unknown");if(_.type==="xero"){const W=V.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+W);te&&te!=="xero-"+W&&(V=te)}return s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",V),"error"),!1}if(D&&D.ok===!1){let Y=D.error_msg||D.error_code||"unknown";return Y=String(Y).slice(0,200),s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",Y),"error"),!1}return s(t("unified-push-ok").replace("{name}",_.name),"success"),!0}catch(T){return s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",T.message||"network"),"error"),!1}finally{k&&(k.disabled=!1,k.classList.remove("loading"))}}async function v(_,g){for(const k of _)await u(k,g)}function b(_,g){const k=document.createElement("div");k.className="pn-push-dropdown",k.id="pn-push-dropdown";const S=(_||[]).map(q=>{const L=!!(g&&q.id===g.id),D=q.method==="download"?t("unified-push-tag-download"):L?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(q.id)+'"><span class="pn-pd-icon">'+c(q)+'</span><span class="pn-pd-name">'+o(q.name)+"</span>"+(D?'<span class="pn-pd-tag">'+o(D)+"</span>":"")+(L?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),T=_&&_.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",_.length))+"</span></div>":"";return k.innerHTML=S+T,k}function C(){const _=document.getElementById("pn-push-dropdown");_&&_.remove()}async function E(){if(document.getElementById("pn-push-dropdown")){C();return}const _=await i()||[],g=l(_),k=b(_,g),S=document.getElementById("pn-push-wrap");S&&S.appendChild(k)}async function m(){const _=await i()||[],g=l(_);if(!g)return;const k=f(),S=k&&(k._historyId||k.history_id);if(S){if(d(k)){s(t("unified-push-disabled-exc"),"warn");return}await u(g,S)}}async function h(_){C();const g=await i()||[],k=f(),S=k&&(k._historyId||k.history_id);if(!S)return;if(d(k)){s(t("unified-push-disabled-exc"),"warn");return}if(_==="__all__"){await v(g,S);return}const T=g.find(q=>q.id===_);T&&(p(_),await u(T,S),B())}async function M(){const _=document.getElementById("drawer-history-save");if(!_||_.querySelector("#pn-push-wrap"))return;const g=document.createElement("div");g.id="pn-push-wrap",g.className="pn-push-wrap",g.dataset.loading="1",_.insertBefore(g,_.firstChild),["btn-push-erp","btn-xero-push"].forEach(D=>{_.querySelectorAll("#"+D).forEach(Y=>{Y.style.display="none"})});const k=await i()||[],S=l(k),T=k.length>0;if(!T)g.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const D=k.length>1;g.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+c(S)+"<span>"+o(t("unified-push-to").replace("{name}",S?S.name:""))+"</span></button>"+(D?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete g.dataset.loading;const q=g.querySelector("#btn-push-default");q&&T&&q.addEventListener("click",m);const L=g.querySelector("#btn-push-arrow");L&&L.addEventListener("click",function(D){D.stopPropagation(),E()}),a||(a=!0,document.addEventListener("click",function(D){const Y=D.target.closest(".pn-pd-item");if(Y){const V=Y.getAttribute("data-cid");h(V);return}D.target.closest("#btn-push-arrow")||C()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",B))}function B(){const _=document.getElementById("pn-push-wrap");_&&(_.remove(),e=null,n=0,M())}function P(){const _=document.getElementById("drawer-history-save");if(!_||!_.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(k=>{_.querySelectorAll("#"+k).forEach(S=>{S.style.display!=="none"&&(S.style.display="none")})});const g=_.querySelectorAll("#pn-push-wrap");if(g.length>1)for(let k=1;k<g.length;k++)g[k].remove()}function H(){try{const _=function(){return document.getElementById("drawer-body")},g=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&M(),P()}),k=_();if(k)g.observe(k,{childList:!0,subtree:!0});else{const S=new MutationObserver(function(){const T=_();T&&(g.observe(T,{childList:!0,subtree:!0}),S.disconnect())});S.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&M(),P()},200)}catch{}}H()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",p=t(r);p&&p!==r&&(i.textContent=p)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const l=document.getElementById("erp-onboard-title"),d=document.getElementById("erp-onboard-body"),f=document.getElementById("erp-onboard-ok"),c=document.getElementById("erp-onboard-later");l&&(l.textContent=t("erp-onboard-title")),d&&(d.textContent=t("erp-onboard-body")),f&&(f.textContent=t("erp-onboard-ok")),c&&(c.textContent=t("erp-onboard-later"))}r();function p(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}p();try{const l=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');l&&l.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}p()}),i.addEventListener("click",function(l){l.target===i&&p()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),p=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||p)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,p=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const l={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+l.replace("{d}",p||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let p=0;for(;;){let l=null;try{const d=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{l=await d.json()}catch{l=null}(!d.ok||!l||!l.ok)&&(l=null)}catch{l=null}if(l){if(p=0,o.onProgress)try{o.onProgress(l.progress||{},l)}catch{}if(l.status==="done"||l.status==="failed"||l.status==="needs_review"||l.status==="needs_mapping")return l}else if(++p>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(d=>setTimeout(d,s))}}})();(function(){let e=!1,n=[],a=[],o=null,s="all",i=[],r={stmt:"",gl:""},p=[];const l=x=>document.getElementById(x);function d(x){if(x==null)return"—";const $=Number(x);return isNaN($)?"—":$.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function f(x){return x?String(x).slice(0,10).split("-").reverse().join("/"):"—"}function c(x){return String(x||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function u(x,$){$=window._currentLang||$||"th";const j={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},G={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},N=j[x]||G;return N[$]||N.th||N.en}function v(x){const $=x==="stmt"?n:a,j=l(`brv2-${x}-name`);if(j)if($.length===0)j.textContent="";else{const N=window._currentLang||"zh",y={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};j.textContent=$.length+(y[N]||" 个文件")}const G=l("brv2-preview-panel");G&&G.style.display!=="none"&&E(x),b()}function b(){const x=l("brv2-toggle-preview"),$=l("brv2-preview-panel"),j=n.length+a.length>0;x&&(x.style.display=j?"":"none"),!j&&$&&($.style.display="none",x&&x.classList.remove("open"))}function C(){E("stmt"),E("gl")}function E(x){const $=l(x==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!$)return;const j=x==="stmt"?n:a,G=window._currentLang||"zh",N={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},y=(N[x]||{})[G]||N[x].zh,F=c(window.t&&window.t("vex-preview-search")||"搜索文件名..."),O=c(window.t&&window.t("vex-preview-clear-all")||"全清"),J=r[x]||"";$.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+c(y)+' <span class="vex-pp-col-count">'+j.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+x+'" type="text" placeholder="'+F+'" value="'+c(J)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+x+'" type="button">'+O+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+x+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+x+'-pg"></div>';const X=l("brv2-pp-search-"+x);X&&X.addEventListener("input",function(se){r[x]=se.target.value,m(x)});const de=l("brv2-pp-clearall-"+x);de&&de.addEventListener("click",function(){x==="stmt"?n.length=0:a.length=0,v(x),D()}),m(x)}function m(x){const $=l("brv2-pp-"+x+"-list"),j=l("brv2-pp-"+x+"-pg");if(!$)return;const G=x==="stmt"?n:a,N=(r[x]||"").toLowerCase(),y=N?G.filter(J=>J.name.toLowerCase().includes(N)):G.slice(),F='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',O='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if($.innerHTML=y.map((J,X)=>'<div class="vex-pp-file-row">'+F+'<span class="vex-pp-fi-name" title="'+c(J.name)+'">'+c(J.name)+'</span><span class="vex-pp-fi-size">'+h(J.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+x+'" data-idx="'+G.indexOf(J)+'" aria-label="remove">'+O+"</button></div>").join(""),$.querySelectorAll(".vex-pp-fi-del").forEach(function(J){J.addEventListener("click",function(){const X=parseInt(J.dataset.idx,10);J.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),v(J.dataset.zone),D()})}),j){const J=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";j.textContent=J.replace("{n}",y.length).replace("{m}",G.length)}}function h(x){return x?x<1024?x+" B":x<1048576?(x/1024).toFixed(1)+" KB":(x/1048576).toFixed(1)+" MB":""}var M="pearnly.brv2.lastAnchorOcr";function B(x){try{var $=x&&x._anchor_ocr;if(!$||typeof $!="object")return;var j={stmt_opening:Number.isFinite(+$.stmt_opening)?+$.stmt_opening:null,gl_opening:Number.isFinite(+$.gl_opening)?+$.gl_opening:null,gl_closing:Number.isFinite(+$.gl_closing)?+$.gl_closing:null,stmt_closing:Number.isFinite(+$.stmt_closing)?+$.stmt_closing:null,ts:Date.now()};localStorage.setItem(M,JSON.stringify(j))}catch{}}function P(){try{var x=localStorage.getItem(M);if(!x)return null;var $=JSON.parse(x);return!$||typeof $!="object"?null:$}catch{return null}}function H(){var x=P();if(x){var $={"brv2-anchor-stmt-opening":x.stmt_opening,"brv2-anchor-gl-opening":x.gl_opening,"brv2-anchor-gl-closing":x.gl_closing,"brv2-anchor-stmt-closing":x.stmt_closing},j=0;Object.keys($).forEach(function(O){var J=document.getElementById(O);if(J&&J.value===""){var X=$[O];if(Number.isFinite(X)){J.value=X.toFixed(2);var de=J.closest&&J.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),j+=1}}});var G=document.getElementById("brv2-anchor-eq"),N=document.getElementById("brv2-anchor-eq-val");if(G&&N&&Number.isFinite(x.stmt_opening)&&Number.isFinite(x.gl_opening)){var y=x.stmt_opening-x.gl_opening;N.textContent=y.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),G.style.display=""}if(j>0){var F=document.getElementById("brv2-anchor-prefill-banner");F&&F.classList.add("show")}}}function _(){var x=document.getElementById("brv2-anchor-prefill-banner");if(x){var $=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(j){var G=document.getElementById(j);if(G){var N=G.closest&&G.closest(".brv2-anchor-cell");N&&N.classList.contains("is-prefilled")&&($=!0)}}),x.classList.toggle("show",$)}}var g=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function k(x,$){return window.t&&window.t(x)||$}function S(x){return String(x??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function T(x){return Number.isFinite(+x)?(+x).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function q(x){var $=document.getElementById("brv2-summary-collapse");if(!(!$||!$.parentNode)){var j=document.getElementById("brv2-anchor-audit"),G=x&&x._anchor_overrides;if(!G||typeof G!="object"||Object.keys(G).length===0){j&&j.parentNode&&j.parentNode.removeChild(j);return}j||(j=document.createElement("div"),j.id="brv2-anchor-audit",j.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",$.parentNode.insertBefore(j,$.nextSibling));var N=g.map(function(y){var F=G[y[0]];if(!F)return"";var O=+F.ocr||0,J=+F.user||0,X=J-O,de=X>0?"+":(X<0,""),se=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+S(k(y[1],y[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+S(T(O))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+S(T(J))+'</td><td style="padding:6px 10px;color:'+se+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+S(de+T(X))+"</td></tr>"}).join("");j.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+S(k("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+S(k("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+S(k("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+S(k("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+S(k("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+N+"</tbody></table>"}}function L(){const x=l("brv2-toggle-preview");x&&!x._reconBound&&(x._reconBound=!0,x.addEventListener("click",function(){const $=l("brv2-preview-panel"),j=l("brv2-toggle-preview-label"),G=$&&$.style.display!=="none";$&&($.style.display=G?"none":""),x.classList.toggle("open",!G),j&&(j.textContent=G?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),G||C()}))}function D(){const x=l("brv2-run-btn"),$=l("brv2-status"),j=n.length>0,G=a.length>0;if(x&&(x.disabled=!(j&&G)),$){const N=window._currentLang||"zh";if(!j&&!G){const y={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};$.textContent=y[N]||y.zh}else if(j)if(G){const y={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};$.textContent=y[N]||y.zh}else{const y={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};$.textContent=y[N]||y.zh}else{const y={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};$.textContent=y[N]||y.zh}}}function Y(x,$,j){const G=l(x),N=l($);!G||!N||(G.addEventListener("click",()=>N.click()),G.addEventListener("keydown",y=>{(y.key==="Enter"||y.key===" ")&&(y.preventDefault(),N.click())}),G.addEventListener("dragover",y=>{y.preventDefault(),G.classList.add("drag-over")}),G.addEventListener("dragleave",()=>G.classList.remove("drag-over")),G.addEventListener("drop",y=>{y.preventDefault(),G.classList.remove("drag-over");const F=Array.from(y.dataTransfer.files||[]);j==="stmt"?n.push(...F):a.push(...F),v(j),D()}),N.addEventListener("change",()=>{const y=Array.from(N.files||[]);j==="stmt"?n.push(...y):a.push(...y),N.value="",v(j),D()}))}function V(x){const $=l("brv2-progress"),j=l("brv2-run-btn"),G=l("brv2-error");$&&($.style.display=x?"":"none"),j&&(j.disabled=x),G&&(G.style.display="none")}function W(x){const $=l("brv2-error");$&&($.textContent=x,$.style.display="",$.scrollIntoView({behavior:"smooth",block:"nearest"})),V(!1),D(),window.showToast&&window.showToast(x,"error")}async function te(){if(n.length===0||a.length===0)return;const x=localStorage.getItem("mrpilot_token")||"",$=window._currentLang||"zh",j=(l("brv2-acct-select")||{}).value||"";A(!1),V(!0);try{const G=new FormData;n.forEach(ae=>G.append("stmt_files",ae)),a.forEach(ae=>G.append("gl_files",ae)),G.append("gl_account",j),G.append("lang",$);const N=parseFloat((l("brv2-anchor-gl-closing")||{}).value),y=parseFloat((l("brv2-anchor-stmt-closing")||{}).value),F=parseFloat((l("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((l("brv2-anchor-gl-opening")||{}).value);Number.isFinite(N)&&G.append("gl_closing_override",N),Number.isFinite(y)&&G.append("stmt_closing_override",y),Number.isFinite(F)&&G.append("stmt_opening_override",F),Number.isFinite(O)&&G.append("gl_opening_override",O);const J=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+x},body:G});let X=null;try{X=await J.json()}catch{X=null}if(X&&X.needs_mapping){V(!1),window.ReconMapping?window.ReconMapping.show(X,{token:x,lang:$,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!J.ok||!X||!X.ok||!X.job_id){V(!1),X&&(X.detail||X.error)?W(_humanizeBackendError(X.detail||X.error,"Error "+J.status)):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=l("brv2-progress-sub"),se=await window._reconPollJob(X.job_id,x,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,$))}});if(se&&se.status==="needs_mapping"&&se.mapping){V(!1),window.ReconMapping?window.ReconMapping.show(se.mapping,{token:x,lang:$,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="needs_review"&&se.review){V(!1),window.ReconReview?window.ReconReview.show(se.review,{token:x,lang:$,jobId:X.job_id,onConfirmed:async function(ae){V(!0);const pe=await window._reconPollJob(ae,x,{onProgress:fe=>{de&&(de.textContent=window._reconProgressText(fe,$))}});await ce(pe)}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="failed"){V(!1),W(u(se.error_code,$));return}await ce(se);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){V(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+x}});let fe=null;try{fe=await pe.json()}catch{fe=null}if(!pe.ok||fe===null||!fe.ok){V(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(fe.gl_accounts||[]).length>1&&re(fe.gl_accounts),o=fe,i=fe.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),B(fe&&fe.summary),V(!1),z(fe),Z();const me=l("brv2-summary-collapse");me&&me.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){V(!1),W(pe.message||"Network error")}}}catch(G){W(G.message||"Network error")}}function re(x){const $=l("brv2-acct-select");if(!$)return;const j=window._currentLang||"zh",G={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[j]||"全部账户";$.innerHTML=`<option value="">${G}</option>`+x.map(N=>`<option value="${c(N)}">${c(N)}</option>`).join(""),$.style.display=""}function A(x){const $=l("brv2-summary-collapse"),j=l("brv2-detail-collapse"),G=l("brv2-export-btn"),N=l("brv2-new-btn"),y=l("brv2-parse-info-wrap");$&&($.style.display=x?"":"none"),j&&(j.style.display=x?"":"none"),G&&(G.style.display=x?"":"none"),N&&(N.style.display=x?"":"none"),!x&&y&&(y.style.display="none");const F=l("brv2-warnings");!x&&F&&(F.style.display="none",F.innerHTML="")}function I(x){const $=l("brv2-parse-info-wrap"),j=l("brv2-parse-info-body");if(!$||!j)return;const G=x.parse_info;if(!G){$.style.display="none";return}const N=window._currentLang||"zh",y={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},F=ce=>(y[ce]||{})[N]||(y[ce]||{}).zh||ce,O=[...(G.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(G.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],J={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&J[ae]){const pe=window._currentLang||"zh";return J[ae][pe]||J[ae].zh}return String(ce.error||"").slice(0,80)},se=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${F("fail")} — ${c(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${F("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${F("warn")}</span>`;j.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${F("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${F("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${F("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${F("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${F("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${F("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${O.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?F("stmt"):F("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${c(ce.file||"")}">${c(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${c(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${se(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,$.style.display=""}async function w(x){const $=localStorage.getItem("mrpilot_token")||"",j=window._currentLang||"zh";try{const G=await fetch("/api/recon/bank-v2/"+x+"/export?lang="+j,{headers:{Authorization:"Bearer "+$}});if(!G.ok){const de=await G.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const N=await G.blob(),F=(G.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),O=F?F[1].replace(/['"]/g,""):"reconciliation.xlsx",J=URL.createObjectURL(N),X=document.createElement("a");X.href=J,X.download=O,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(J)}catch(G){window.showToast&&window.showToast("Export error: "+G.message,"error")}}function R(x,$){const j=l("brv2-summary-collapse");let G=l("brv2-warnings");const N=window._currentLang||"zh",y={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[N]||"⏭ ",F=[];if(($||[]).forEach(O=>F.push(y+" "+O)),(x||[]).forEach(O=>F.push(O)),!F.length){G&&(G.style.display="none");return}if(!G)if(G=document.createElement("div"),G.id="brv2-warnings",j&&j.parentNode)j.parentNode.insertBefore(G,j);else return;G.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",G.innerHTML=F.map(O=>"<div>"+c(O)+"</div>").join("")}function z(x){I(x),R(x.warnings||[],x.skipped_files||[]),!x.ok&&x.error&&window.showToast&&window.showToast(x.error,"error");const $=x.stats||{},j=x.summary||{},G=$.matched||0,N=($.gl_debit_only||0)+($.gl_credit_only||0),y=($.stmt_withdrawal_only||0)+($.stmt_deposit_only||0),F=Number(j.formula_diff||0),O=Math.abs(F)<.05;l("brv2-kpi-matched")&&(l("brv2-kpi-matched").textContent=G),l("brv2-kpi-diff")&&(l("brv2-kpi-diff").textContent=d(F)),l("brv2-kpi-unmatched")&&(l("brv2-kpi-unmatched").textContent=N+y);const J=l("brv2-kpi-diff-icon");J&&(J.style.background=O?"#d1fae5":"#fee2e2",J.style.color=O?"#065f46":"#b91c1c");const X=l("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=O?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+d(F)}const de=l("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",fe={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=fe.replace("{n}",i.length)}function se(pe,fe,me){const ge=l(pe);ge&&(ge.textContent=(me&&fe>0?"(":"")+d(me?-fe:fe)+(me&&fe>0?")":""))}se("brf-gl-close",j.gl_closing||0),se("brf-open-diff",j.opening_diff||0),se("brf-gl-debit-only",j.gl_debit_only_amount||0,!0),se("brf-gl-credit-only",j.gl_credit_only_amount||0),se("brf-stmt-wd-only",j.stmt_withdrawal_only_amount||0,!0),se("brf-stmt-dep-only",j.stmt_deposit_only_amount||0),se("brf-calc-close",j.formula_stmt_closing||0),se("brf-stmt-close",j.stmt_closing||0),l("brf-diff")&&(l("brf-diff").textContent=d(F));const ce=l("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",O);const ae=l("brv2-export-btn");ae&&(ae.onclick=()=>{o&&w(o.task_id)}),q(j),A(!0),K()}function K(){const x=l("brv2-tbody");if(!x)return;const $=i.filter(y=>s==="all"?!0:s==="matched"?y.match_status==="matched":s==="gl_only"?y.match_status.startsWith("gl_"):s==="stmt_only"?y.match_status.startsWith("stmt_"):!0);if($.length===0){const y={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";x.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${y}</td></tr>`;return}const j=window._currentLang||"zh",G={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[j],N={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[j];x.innerHTML=$.map(y=>{const F=y.match_status,O=y.match_layer;let J="",X="";F==="matched"?(O===1&&(J="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),O===2&&(J="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),O===3&&(J="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):F==="gl_debit_only"||F==="gl_credit_only"?(J="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(J="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[j]||"账单"}</span>`);let de="";return y.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${c(G)}">⚠</span>`,J+=" brv2-row-warn"),y.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${c(N)}">◌</span>`,J.includes("brv2-row-warn")||(J+=" brv2-row-warn-soft")),`<tr class="${J.trim()}">
              <td>${X}${de}</td>
              <td>${c(f(y.stmt_date))}</td>
              <td title="${c(y.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(y.stmt_desc)}</td>
              <td class="num">${y.stmt_withdrawal?d(y.stmt_withdrawal):""}</td>
              <td class="num">${y.stmt_deposit?d(y.stmt_deposit):""}</td>
              <td>${c(f(y.gl_date))}</td>
              <td title="${c(y.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c(y.gl_doc_no)}</td>
              <td class="num">${y.gl_debit?d(y.gl_debit):""}</td>
              <td class="num">${y.gl_credit?d(y.gl_credit):""}</td>
              <td>${O?"L"+O:"—"}</td>
            </tr>`}).join("")}async function Z(){const x=localStorage.getItem("mrpilot_token")||"";try{const j=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+x}})).json();ee(j.tasks||[])}catch{const j=l("brv2-history-empty"),G=window._currentLang||"zh",N={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[G]||"加载失败";j&&(j.textContent=N,j.style.display="");const y=l("brv2-history-table-wrap");y&&(y.style.display="none")}}const le=10;let ie=1;function U(){const x=l("brv2-history-pager"),$=l("brv2-history-pager-info"),j=l("brv2-history-prev"),G=l("brv2-history-next");if(!x)return;if(p.length<=le){x.style.display="none";return}x.style.display="";const N=Math.ceil(p.length/le);$&&($.textContent=ie+" / "+N),j&&(j.disabled=ie<=1),G&&(G.disabled=ie>=N)}function Q(){const x=l("brv2-history-prev"),$=l("brv2-history-next");x&&!x._brv2Bound&&(x._brv2Bound=!0,x.addEventListener("click",()=>{ie>1&&(ie--,ee(p))})),$&&!$._brv2Bound&&($._brv2Bound=!0,$.addEventListener("click",()=>{const j=Math.ceil(p.length/le);ie<j&&(ie++,ee(p))}))}function ee(x){x!==void 0&&(p=x||[],ie=1);const $=p,j=l("brv2-history-empty"),G=l("brv2-history-table-wrap"),N=l("brv2-history-tbody");if(!N)return;const y=window._currentLang||"zh";if(!$.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[y]||"暂无对账记录";j&&(j.textContent=ae,j.style.display=""),G&&(G.style.display="none"),U();return}j&&(j.style.display="none"),G&&(G.style.display="");const F=Math.ceil($.length/le);ie>F&&(ie=F);const O=(ie-1)*le,J=$.slice(O,O+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';N.innerHTML="",J.forEach(ae=>{const pe=Number(ae.formula_diff||0),fe=Math.abs(pe)<.05,me=(ae.stmt_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ye=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const Ne=document.createElement("td");Ne.textContent=ye;const Te=document.createElement("td");Te.className="glv-history-file",Te.title=me+" + "+ge,Te.textContent=me+" + "+ge;const He=document.createElement("td");He.className="glv-num",He.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const it=document.createElement("td");it.className="glv-num",it.textContent=ae.matched_count||0;const rt=document.createElement("td");rt.className="glv-num",rt.textContent=ae.unmatched_gl||0;const lt=document.createElement("td");lt.className="glv-num",lt.textContent=ae.unmatched_stmt||0;const Oe=document.createElement("td");Oe.className="glv-num",Oe.style.color=fe?"#059669":"#dc2626",Oe.textContent=fe?"✓":d(pe);const Ae=document.createElement("td");Ae.className="glv-history-actions";const ct=(ke,St,Ct,kn)=>{const Ie=document.createElement("button");return Ie.type="button",Ie.title=St,Ie.setAttribute("aria-label",St),Ct&&(Ie.className=Ct),Ie.innerHTML=ke,Ie.onclick=xn=>{xn.stopPropagation(),kn()},Ie},yn={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[y]||"删除?",bn={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[y]||"加载",wn={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[y]||"导出",_n={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[y]||"删除";Ae.appendChild(ct(de,bn,"",()=>oe(ae.id,X))),Ae.appendChild(ct(se,wn,"",()=>w(ae.id))),Ae.appendChild(ct(ce,_n,"glv-del",async()=>{await showConfirm(yn,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[Ne,Te,He,it,rt,lt,Oe,Ae].forEach(ke=>xe.appendChild(ke)),xe.style.cursor="pointer",xe.addEventListener("click",async ke=>{ke.target.closest(".glv-del")||ke.target.closest("button")||await oe(ae.id,X)}),N.appendChild(xe)}),U(),ne()}function ne(){const x=((l("brv2-hist-search")||{}).value||"").trim().toLowerCase(),$=l("brv2-history-tbody");$&&$.querySelectorAll("tr").forEach(j=>{j.dataset.taskId&&(j.style.display=!x||j.textContent.toLowerCase().includes(x)?"":"none")})}async function oe(x,$){try{const G=await(await fetch("/api/recon/bank-v2/"+x,{headers:{Authorization:"Bearer "+$}})).json();if(!G.ok)return;o={task_id:G.task_id,...G},i=G.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(N=>N.classList.toggle("active",N.dataset.filter==="all")),z(o)}catch{}}function ue(){if(e){Z();return}e=!0,Y("brv2-stmt-zone","brv2-stmt-input","stmt"),Y("brv2-gl-zone","brv2-gl-input","gl");const x=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function $(){const O=parseFloat((l("brv2-anchor-stmt-opening")||{}).value),J=parseFloat((l("brv2-anchor-gl-opening")||{}).value),X=l("brv2-anchor-eq"),de=l("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(O)&&Number.isFinite(J)){const se=O-J;de.textContent=se.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}x.forEach(O=>{const J=l(O);J&&(J.addEventListener("input",$),J.addEventListener("input",()=>{const X=J.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),_()}))}),H();const j=l("brv2-run-btn");j&&j.addEventListener("click",te);const G=l("brv2-reset-btn");G&&G.addEventListener("click",()=>{o=null,i=[],n=[],a=[],v("stmt"),v("gl"),D(),A(!1);const O=l("brv2-acct-select");O&&(O.style.display="none"),x.forEach(de=>{const se=l(de);if(se){se.value="";const ce=se.closest&&se.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const J=l("brv2-anchor-eq");J&&(J.style.display="none");const X=l("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const N=l("brv2-new-btn");N&&N.addEventListener("click",()=>{o=null,i=[],n=[],a=[],v("stmt"),v("gl"),D(),A(!1)});const y=l("brv2-filter-tabs");y&&y.addEventListener("click",O=>{O.stopPropagation();const J=O.target.closest(".brv2-filter-btn");J&&(s=J.dataset.filter,y.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===J)),K())}),L(),Q();const F=l("brv2-hist-search");F&&F.addEventListener("input",ne),Z(),D(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(O=>O.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){D(),v("stmt"),v("gl"),o&&z(o),ee()}})}window._loadBankReconV2Panel=function(x){const $=x?document.getElementById(x):null;$&&$.id!=="recon-pane-bank"&&($.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{l("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const d=document.getElementById("general-tz"),f=document.getElementById("general-date"),c=document.getElementById("general-number");if(!(!d||!f||!c))try{d.value=localStorage.getItem(n)||s.tz,f.value=localStorage.getItem(a)||s.date,c.value=localStorage.getItem(o)||s.number}catch{d.value=s.tz,f.value=s.date,c.value=s.number}}async function r(){const d=document.getElementById("btn-save-general"),f=document.getElementById("general-save-msg");if(!d)return;const c=d.innerHTML;d.disabled=!0,d.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",f&&(f.textContent="",f.classList.remove("error"));try{const u=(document.getElementById("general-tz")||{}).value||s.tz,v=(document.getElementById("general-date")||{}).value||s.date,b=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,u),localStorage.setItem(a,v),localStorage.setItem(o,b)}catch{}window._pearnlyGeneral={tz:u,date_format:v,number_format:b},f&&(f.textContent=t("msg-saved")||"已保存")}catch{f&&(f.textContent=t("msg-save-failed")||"保存失败",f.classList.add("error"))}finally{d.disabled=!1,d.innerHTML=c,setTimeout(function(){f&&(f.textContent="")},3e3)}}function p(){const d=document.getElementById("btn-save-general");if(!d){setTimeout(p,200);return}d._pearnlyGenBound||(d._pearnlyGenBound=!0,d.addEventListener("click",r),i())}function l(){i();const d=document.getElementById("general-lang");if(d){const f=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";d.value=f}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",p):p(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",l)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(p){const l=p.dataset.collapsible;r[l]?p.classList.add("collapsed"):p.classList.remove("collapsed")})}function i(r){const p=a();p[r]=!p[r],o(p),s()}(function(){const p=a();let l=!1;p.sales===void 0&&(p.sales=!1,l=!0),p.expense===void 0&&(p.expense=!0,l=!0),l&&o(p)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const p=n[r];if(!p)return;const l=a();l[p]&&(l[p]=!1,o(l),s())}})();const Ra=`
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
    </div>`;function At(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=Ra;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,At();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let we=[];window._erpEndpoints=we;let Fe=null;async function ot(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,cn()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return ot()};async function ln(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const p=[];p.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&p.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&p.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&p.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=p.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function cn(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&we.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=we.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),ln(),e.innerHTML=we.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const p=s.enabled!==!1,l=[];s.is_default&&l.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&l.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),p||l.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const d=[];return s.success_count>0&&d.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&d.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=we.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,p=document.createElement("div");p.className="erp-limit-hint",r==="free"?p.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:p.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(p)}}function Fa(e){Fe=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),p=document.getElementById("ep-auto-push"),l=document.getElementById("ep-test-result");l.style.display="none",l.textContent="";const d=document.getElementById("ep-save-error");if(d&&d.remove(),e){const c=we.find(u=>u.id===e);if(!c)return;o.value=c.name||"",s.value=(c.config||{}).url||"",i.value=(c.config||{})._token_set&&c.config.token||"",i.placeholder=(c.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!c.is_default,p.checked=!!c.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=we.length===0,p.checked=!0;const f=p.closest(".form-switch-row");if(p.disabled=!1,f){f.classList.remove("disabled-plus"),f.title="",f.style.cursor="",f.onclick=null;const c=f.querySelector(".plus-badge");c&&c.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function dn(){document.getElementById("endpoint-modal").style.display="none",Fe=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function pn(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function un(){const e=document.getElementById("ep-name").value.trim(),n=pn(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function za(){const{url:e,config:n}=un(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function Na(){const e=un(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){jt(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(Fe?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(Fe)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const p=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof p=="string"?p:JSON.stringify(p))}dn(),showToast(t("ep-save-ok")),ot()}catch(i){jt(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function jt(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function Oa(e){const n=we.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),ot()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=ot;window.loadErpTodayStats=ln;window.renderErpEndpointsList=cn;window.openEndpointModal=Fa;window.closeEndpointModal=dn;window.saveEndpoint=Na;window.deleteEndpoint=Oa;window.testEndpointConnection=za;window._sanitizeUrl=pn;async function fn(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function Va(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){fn(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(T=>T.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),p=new Date(o.created_at).toLocaleString(),l=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),d=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),f=o.response_body||t("erp-receipt-no-tech"),c=o.status==="success";let u=typeof f=="string"?f:JSON.stringify(f,null,2);if(c)try{const T=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},q=T.row_count||(Array.isArray(T.imported_rows)?T.imported_rows.length:0);q>0&&(u=t("log-push-rows").replace("{n}",String(q)))}catch{}const v=(o.external_doc_no||"").trim(),b=(o.external_url||"").trim(),C=(o.external_doc_hint||"").trim(),E=(o.ocr_buyer_name||"").trim()||o.client_name||"-",m=o.seller_name||"-";let h="-";const M=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN(M)&&(h=M.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const B=c?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),P=c?"✓":"✗",H=[],_=(T,q)=>{H.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(T)}</span>
                    <span class="erp-receipt-val">${q}</span>
                </div>`)};if(_(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),_(t("erp-receipt-erp-name"),escapeHtml(i)),c){let T;v?T=`<strong class="erp-receipt-docno">${escapeHtml(v)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(v)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:T=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,_(t("erp-receipt-doc-no"),T)}_(t("erp-receipt-client"),escapeHtml(E)),_(t("erp-receipt-seller"),escapeHtml(m)),c&&_(t("erp-receipt-amount"),escapeHtml(h)),_(t("erp-receipt-time"),escapeHtml(p)),_(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let g="";c&&b?g=`<a class="erp-receipt-primary-btn" href="${escapeHtml(b)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:c&&v&&(g=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(v)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let k="";if(c&&v&&C){const T="erp-receipt-hint-"+C,q=t(T);q&&q!==T&&(k=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(q)}</span></div>`)}let S="";if(!c){const T=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),q=T?T[0]:"",L=typeof currentLang=="string"&&currentLang||window._currentLang||"th",Y=o.error_friendly&&o.error_friendly[L]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),V=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),W=!!(o.history_id&&o.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),V&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),W&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),S=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${q?`<div class="erp-receipt-errcode">${escapeHtml(q)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(Y)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${c?"ok":"fail"}">${P}</span>
                    ${escapeHtml(B)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(l)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${H.join("")}
            </div>

            ${k}
            ${g?`<div class="erp-receipt-primary-wrap">${g}</div>`:""}
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
                    <pre>${escapeHtml(d)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t("log-detail-response-human"))}</div>
                    <pre>${escapeHtml(u)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=fn;window.showLogDetail=Va;let Be={key:"all",val:""},Ee=new Set;window._erpSelected=Ee;async function ze(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats();try{const a=new URLSearchParams({limit:"30"});Be.key==="status"&&a.set("status",Be.val),Be.key==="trigger"&&a.set("trigger",Be.val),Be.key==="adapter"&&a.set("adapter",Be.val);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(d){return d.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){ze(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const p='<div class="erp-log-row erp-log-row-header" data-log-header>'+(i.filter(function(d){var f=d.status==="failed"&&d.next_retry_at&&new Date(d.next_retry_at).getTime()>Date.now()-6e4;return!f}).map(function(d){return d.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=p+i.map(d=>{const f=new Date(d.created_at),c=`${String(f.getMonth()+1).padStart(2,"0")}-${String(f.getDate()).padStart(2,"0")} ${String(f.getHours()).padStart(2,"0")}:${String(f.getMinutes()).padStart(2,"0")}`,u=d.status==="failed"&&d.next_retry_at&&new Date(d.next_retry_at).getTime()>Date.now()-6e4;let v,b,C;d.status==="pending"?(v="retrying",b="⟳",C=t("erp-status-pending")):d.status==="success"?(v="ok",b="✓",C=t("erp-status-success")):d.status==="skipped_dup"?(v="skipped",b="⏭",C=t("erp-status-skipped")):u?(v="retrying",b="↻",C=t("erp-status-retrying")):(v="fail",b="✗",C=t("erp-status-failed"));let E;d.trigger==="auto"?E=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:d.trigger==="retry"?E=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:E=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let m="";const h=d.retry_count||0,M=d.max_retries||3;if(u){const Y=new Date(d.next_retry_at).getTime()-Date.now(),V=Math.max(0,Math.round(Y/6e4)),W=V<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:V});m=`${t("erp-retry-attempt",{n:h,max:M})} · ${W}`}else d.status==="failed"&&h>=M&&!d.next_retry_at&&(m=t("erp-retry-exhausted",{n:h}));const B=d.status==="failed"&&!u?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(d.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",P=!u,H=Ee.has(d.id)?"checked":"",_=P?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(d.id)}" ${H}>`:'<span class="erp-log-cb-spacer"></span>',g=(d.ocr_buyer_name||"").trim()||(d.client_name||"").trim(),k=g?`<span class="log-client" title="${escapeHtml(g)}">${escapeHtml(g.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,S=d.workspace_name?`<span class="log-workspace">${escapeHtml((d.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,T=d.endpoint_name?`<span class="log-erp">${escapeHtml((d.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,q=(d.external_doc_no||"").trim(),L=(d.external_url||"").trim();let D;return L?D=`<span class="log-doc"><a href="${escapeHtml(L)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(q||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:q?D=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(q)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(q.substring(0,18))}</span>`:d.status==="success"?D=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:D='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${v}" data-log-detail="${escapeHtml(d.id)}">
                    ${_}
                    <span class="log-time">${c}</span>
                    <span class="log-status" title="${escapeHtml(C+(m?" · "+m:""))}">${b}</span>
                    ${E}
                    <span class="log-invoice">${escapeHtml(d.invoice_no||"-")}</span>
                    ${S}
                    ${k}
                    <span class="log-seller">${escapeHtml((d.seller_name||"").substring(0,20))}</span>
                    ${T}
                    ${D}
                    <span class="log-http">HTTP ${d.http_status||"-"}</span>
                    <span class="log-elapsed">${d.elapsed_ms}ms</span>
                    <span class="log-actions">${B}</span>
                </div>
            `}).join("");const l=new Set(i.map(d=>d.id));for(const d of Array.from(Ee))l.has(d)||Ee.delete(d);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function mn(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),ze(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),mn(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const f=i.dataset.logCb;i.checked?Ee.add(f):Ee.delete(f),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const f=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(u){u.checked=f;const v=u.dataset.logCb;f?Ee.add(v):Ee.delete(v)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),Ee.clear(),document.querySelectorAll(".erp-log-cb").forEach(f=>{f.checked=!1}),window._refreshErpBatchBar();return}const p=n.target.closest("[data-log-detail]");if(p){if(n.target.closest("[data-log-cb]"))return;const f=n.target.closest("[data-copy-doc]");if(f){n.stopPropagation(),window.copyErpDocNo(f.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(p.dataset.logDetail);return}const l=n.target.closest(".chip-filter");if(l){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(f=>f.classList.remove("active")),l.classList.add("active"),Be={key:l.dataset.filterKey,val:l.dataset.filterVal},ze();return}if(n.target.closest("#btn-refresh-logs")){const f=n.target.closest("#btn-refresh-logs");f.classList.add("spinning"),setTimeout(()=>f.classList.remove("spinning"),600),ze();return}const d=n.target.closest(".auto-nav-item");if(d&&d.dataset.autoTab){switchAutomationTab(d.dataset.autoTab);return}})})();window.loadErpLogs=ze;window.retryPushLog=mn;function vn(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function hn(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function gn(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),hn()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),gn()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),vn()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=vn;window._runErpBatchRetry=hn;window._runErpBatchDelete=gn;(function(){let e=null,n=!1;function a(){if(e)return e;const p=document.createElement("div");p.id="line-email-modal",p.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",p.innerHTML=`
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
        `,document.body.appendChild(p),e=p;const l=p.querySelector("#line-email-input"),d=p.querySelector("#line-email-submit-btn"),f=p.querySelector("#line-email-err");async function c(){f.textContent="";const u=(l.value||"").trim().toLowerCase();if(!u||u.indexOf("@")<0||u.split("@")[1].indexOf(".")<0){f.textContent=t("line-email-err-invalid");return}d.disabled=!0,d.style.opacity="0.6";try{const v=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:u})});if(!v.ok)throw new Error("http_"+v.status);const b=await v.json();b.token&&localStorage.setItem("mrpilot_token",b.token),typeof showToast=="function"&&showToast(b.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{f.textContent=t("line-email-err-failed"),d.disabled=!1,d.style.opacity="1"}}return d.addEventListener("click",c),l.addEventListener("keydown",function(u){u.key==="Enter"&&c()}),p}function o(){if(!e)return;const p=e.querySelector("#line-email-title-h"),l=e.querySelector("#line-email-sub-p"),d=e.querySelector("#line-email-input"),f=e.querySelector("#line-email-submit-btn");p&&(p.textContent=t("line-email-title")),l&&(l.textContent=t("line-email-sub")),d&&(d.placeholder=t("line-email-placeholder")),f&&(f.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const p=e.querySelector("#line-email-input");p&&setTimeout(function(){p.focus()},100)}async function i(){const p=localStorage.getItem("mrpilot_token");if(p)try{const l=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+p}});if(!l.ok)return;const d=await l.json();d&&d.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(f){let c=0;return f.length>=8&&c++,f.length>=12&&c++,/[a-zA-Z]/.test(f)&&/\d/.test(f)&&c++,/[^a-zA-Z0-9]/.test(f)&&c++,Math.min(3,c)}function n(f,c){const u=document.getElementById("cpw-msg");u&&(u.textContent=f,u.className="cpw-msg "+(c||""))}function a(f){return typeof t=="function"?t(f):f}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(c=>{const u=document.getElementById(c);u&&(u.value="",u.setAttribute("readonly","readonly"))});const f=document.getElementById("cpw-strength-bar");f&&(f.style.width="0%",f.className="cpw-strength-bar"),n("","")}async function i(){const f=document.getElementById("btn-change-pw"),c=document.getElementById("cpw-old"),u=document.getElementById("cpw-new"),v=document.getElementById("cpw-confirm"),b=document.getElementById("cpw-strength-bar");if(!f||!c||!u||!v)return;const C=c.value,E=u.value,m=v.value;if(!C||!E||!m){n(a("settings-change-pw-empty"),"error");return}if(E.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(E)&&/\d/.test(E))){n(a("settings-change-pw-too-weak"),"error");return}if(E!==m){n(a("settings-change-pw-mismatch"),"error");return}f.disabled=!0;const h=f.textContent;f.textContent=a("settings-change-pw-submitting"),n("","");try{const M=localStorage.getItem("mrpilot_token"),B=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+M},body:JSON.stringify({old_password:C,new_password:E})}),P=await B.json().catch(()=>({}));if(B.ok&&P.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),c.value="",u.value="",v.value="",b&&(b.style.width="0%",b.className="cpw-strength-bar");else{const H=P.detail||"";let _=a("settings-change-pw-success");H==="wrong_old_password"?_=a("settings-change-pw-wrong-old"):H==="password_too_short"?_=a("settings-change-pw-too-short"):H==="password_too_weak"?_=a("settings-change-pw-too-weak"):_=H||"Error",n(_,"error")}}catch(M){console.error("change_password",M),n("Network error","error")}finally{f.disabled=!1,f.textContent=h}}function r(){o||(o=!0,document.addEventListener("click",f=>{if(!f.target||!f.target.closest)return;const c=f.target.closest(".cpw-eye");if(c){const u=document.getElementById(c.dataset.target);u&&(u.type=u.type==="password"?"text":"password");return}if(f.target.closest("#cpw-forgot-link")){f.preventDefault(),p();return}if(f.target.closest("#btn-change-pw")){i();return}f.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",f=>{if(f.target&&f.target.id==="cpw-new"){const c=document.getElementById("cpw-strength-bar");if(!c)return;const u=e(f.target.value),v=["0%","33%","66%","100%"],b=["","weak","medium","strong"];c.style.width=v[u],c.className="cpw-strength-bar "+b[u]}}),document.addEventListener("focusin",f=>{f.target&&["cpw-old","cpw-new","cpw-confirm"].includes(f.target.id)&&f.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function p(){const f=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),c=f&&f.username?f.username:"",u=l(c);let v=document.getElementById("cpw-forgot-overlay");v&&v.remove(),v=document.createElement("div"),v.id="cpw-forgot-overlay",v.className="cpw-forgot-overlay",v.innerHTML=`
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
        `,document.body.appendChild(v);const b=()=>v.remove();v.querySelector("#cpw-forgot-close").addEventListener("click",b),v.querySelector("#cpw-forgot-cancel").addEventListener("click",b),v.addEventListener("click",C=>{C.target===v&&b()}),v.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const C=v.querySelector("#cpw-forgot-send"),E=v.querySelector("#cpw-forgot-msg");C.disabled=!0;const m=C.textContent;C.textContent=a("cpw-forgot-sending");try{const h=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:c})}),M=await h.json().catch(()=>({}));h.ok?(E.textContent=a("cpw-forgot-success"),E.className="cpw-forgot-msg success",C.style.display="none",v.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(E.textContent=M.detail||a("cpw-forgot-fail"),E.className="cpw-forgot-msg error",C.disabled=!1,C.textContent=m)}catch{E.textContent=a("cpw-forgot-fail"),E.className="cpw-forgot-msg error",C.disabled=!1,C.textContent=m}})}function l(f){if(!f||!f.includes("@"))return f||"";const[c,u]=f.split("@");return c.length<=2?c+"****@"+u:c.slice(0,2)+"****@"+u}function d(f){return f==null?"":String(f).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),p=r&&r.detail;let l="";if(typeof p=="string"?l=p:p&&typeof p=="object"&&(l=p.code||""),console.warn("[heartbeat] session revoked",l),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),l==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const d=l==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(d),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function st(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const p=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",l=r.is_active===!1?"team-status-off":"team-status-on",d=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",f=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Ua(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),p=document.getElementById("add-emp-submit"),l=(o.value||"").trim(),d=(s.value||"").trim(),f=i.value||"";if(r.textContent="",r.classList.remove("error"),!l||l.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(l)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(d&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(f.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(f)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(f)&&/\d/.test(f))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}p.disabled=!0,p.textContent=t("msg-saving")||"保存中...";try{const c={username:l,password:f};d&&(c.email=d);const u=await apiPost("/api/team/employees",c),v=u?await u.json().catch(()=>({})):{};if(u&&u.ok&&v&&v.ok){showToast(t("team-added")||"员工已添加","success"),n(),st();return}const b=v&&v.detail||"unknown",C={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=C[b]||(t("team-create-failed")||"创建失败")+" ("+b+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{p.disabled=!1,p.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Ga(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){st();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Ka(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),st();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function Ja(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const p=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",l=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(p.replace("{ch}",l),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Ua();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Ga(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Ka(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),Ja(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=st;function Ya(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Ya;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
