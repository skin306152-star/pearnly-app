(function(){const n=[];function a(s){try{n.push(Object.assign({ts:Date.now()},s)),n.length>200&&n.shift();try{typeof window._tcOnNewLog=="function"&&window._tcOnNewLog(s)}catch{}}catch{}}window._pearnlyTcLogs=n,window._pearnlyTcPush=a,window.addEventListener("error",function(s){s.target&&s.target!==window&&(s.target.src||s.target.href)||a({type:"js_error",summary:String(s.message||"JS Error").slice(0,200),detail:{file:s.filename||"",line:s.lineno||0,col:s.colno||0,stack:s.error&&s.error.stack?String(s.error.stack).slice(0,2e3):null}})},!0),window.addEventListener("unhandledrejection",function(s){const i=s.reason,r=i&&i.message?i.message:String(i||"Promise rejected");a({type:"promise_error",summary:String(r).slice(0,200),detail:{stack:i&&i.stack?String(i.stack).slice(0,2e3):null}})});const o=window.fetch;typeof o=="function"&&(window.fetch=function(){const s=arguments,i=Date.now(),r=typeof s[0]=="string"?s[0]:s[0]&&s[0].url||"?",u=s[1]&&s[1].method||"GET",l=String(r).split("?")[0];return o.apply(this,s).then(function(d){const c=Date.now()-i;if(d.ok)c>2500&&a({type:"api_slow",summary:u+" "+l+" → 慢 "+c+"ms",detail:{url:r,method:u,status:d.status,elapsed_ms:c}});else{let p="";try{d.clone().text().then(function(m){p=String(m||"").slice(0,500),a({type:"api_error",summary:u+" "+l+" → "+d.status+" ("+c+"ms)",detail:{url:r,method:u,status:d.status,elapsed_ms:c,body_preview:p}})}).catch(function(){a({type:"api_error",summary:u+" "+l+" → "+d.status+" ("+c+"ms)",detail:{url:r,method:u,status:d.status,elapsed_ms:c,body_preview:"(read failed)"}})})}catch{a({type:"api_error",summary:u+" "+l+" → "+d.status+" ("+c+"ms)",detail:{url:r,method:u,status:d.status,elapsed_ms:c}})}}return d}).catch(function(d){const c=Date.now()-i;throw a({type:"api_fail",summary:u+" "+l+" → 网络失败 ("+c+"ms)",detail:{url:r,method:u,elapsed_ms:c,error:String(d&&d.message||d)}}),d})}),["error","warn"].forEach(function(s){const i=console[s];typeof i=="function"&&(console[s]=function(){try{const r=[];for(let u=0;u<arguments.length;u++){const l=arguments[u];if(typeof l=="string")r.push(l);else if(l&&l instanceof Error)r.push(l.message);else try{r.push(JSON.stringify(l).slice(0,300))}catch{r.push(String(l))}}a({type:"console_"+s,summary:r.join(" ").slice(0,200),detail:{full:r.join(" ").slice(0,1500)}})}catch{}return i.apply(console,arguments)})})})();window.__i18nSubs=window.__i18nSubs||[];window.subscribeI18n=function(e,n){if(typeof n!="function"){console.warn("[i18n] subscribeI18n: fn must be function · name="+e);return}const a=window.__i18nSubs.find(o=>o.name===e);if(a){a.fn=n;return}window.__i18nSubs.push({name:String(e||"?"),fn:n})};window.currentLang=localStorage.getItem("mrpilot_lang")||"th";window._currentLang=window.currentLang;window.currentRoute="ocr";window._userInfo=null;window._quota=null;window._contact=null;window._selectedFiles=[];window._results=[];window._sortKey=null;window._sortDir="asc";window._searchKeyword="";window._drawerIdx=-1;window._drawerAlreadyPushed=!1;window._historyState={page:0,pageSize:20,total:0,keyword:"",range:90,items:[],loading:!1};window._historySelected=new Set;window._erpEndpoints=[];window.token=localStorage.getItem("mrpilot_token");function xn(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_upload_files)return e.limits.max_upload_files;const n=_userInfo&&_userInfo.plan||"trial";return _userInfo&&_userInfo.is_super_admin?9999:{admin:9999,lifetime:1e3,yearly:800,monthly:500,trial:30,enterprise:1e3,firm:800,pro:500,plus:30,free:30}[n]||30}catch{return 30}}function En(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_pages_per_file)return e.limits.max_pages_per_file;if(_userInfo&&_userInfo.is_super_admin)return 999;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?100:50}catch{return 50}}function In(){try{const e=window._planState;if(e&&e.limits&&e.limits.max_mb_per_file)return e.limits.max_mb_per_file;if(_userInfo&&_userInfo.is_super_admin)return 500;const n=_userInfo&&_userInfo.plan||"trial";return n==="lifetime"||n==="enterprise"?200:100}catch{return 100}}function Xe(e,n){let a=I18N[currentLang]&&I18N[currentLang][e]||e;if(n)for(const o in n)a=a.replace("{"+o+"}",n[o]);return a}function Bn(e){return String(e??"").replace(/[&<>"']/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[n])}function Ln(e,n){n=n||14;const o={refresh:'<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/>',cache:'<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',wifiOff:'<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',wifiOn:'<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',check:'<path d="M20 6 9 17l-5-5"/>',alert:'<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',folder:'<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',api:'<path d="M3 6.5a4.5 4.5 0 0 1 9 0v11a4.5 4.5 0 0 1-9 0Z"/><path d="M12 17.5a4.5 4.5 0 0 0 9 0v-11a4.5 4.5 0 0 0-9 0Z"/>',copy:'<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',minus:'<line x1="5" y1="12" x2="19" y2="12"/>',sparkle:'<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>'}[e]||"";return`<svg width="${n}" height="${n}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; flex-shrink: 0;">${o}</svg>`}function Ze(){if(!document.getElementById("pn-session-revoked-modal")){var e=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th",n={zh:"账号已在其他设备登录",en:"Signed in on another device",th:"บัญชีถูกเข้าใช้งานจากอุปกรณ์อื่น",ja:"他のデバイスでサインインされました"},a={zh:`你的账号刚刚在另一台设备上登录
当前设备已自动退出，请重新登录继续使用。`,en:`Your account was just signed in on another device.
This device has been logged out automatically.`,th:`บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์อื่น
ระบบออกจากอุปกรณ์นี้โดยอัตโนมัติแล้ว กรุณาเข้าสู่ระบบใหม่`,ja:`お使いのアカウントが別のデバイスでサインインされました。
このデバイスは自動的にログアウトされました。`},o={zh:"确定，去登录",en:"OK, Sign in",th:"ตกลง เข้าสู่ระบบ",ja:"OK、ログイン"},s=n[e]?e:"th",i=document.createElement("div");i.id="pn-session-revoked-modal",i.style.cssText="position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px;",i.innerHTML='<div style="background:#fff;border-radius:14px;padding:32px 24px 24px;max-width:360px;width:100%;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center;"><div style="width:52px;height:52px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;margin:0 auto 18px;flex-shrink:0;"><svg width="26" height="26" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r=".5" fill="#DC2626"/></svg></div><div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:10px;line-height:1.4;">'+n[s]+'</div><div style="font-size:13px;color:#6B7280;line-height:1.7;margin-bottom:24px;white-space:pre-line;">'+a[s]+'</div><button id="pn-srm-ok" style="width:100%;padding:11px 0;background:#111111;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">'+o[s]+"</button></div>",document.body.appendChild(i),document.getElementById("pn-srm-ok").addEventListener("click",function(){window.location.href="/"})}}function Qe(){try{if(typeof window.getActiveWorkspaceClientId=="function"){const e=window.getActiveWorkspaceClientId();if(e!=null)return{"X-Workspace-Client-Id":String(e)}}}catch{}return{}}async function Sn(e){const n=await fetch(e,{headers:{Authorization:"Bearer "+token,...Qe()}});if(n.status===401||n.status===403){const a=await n.json().catch(()=>({})),o=a&&a.detail;let s="";if(typeof o=="string"?s=o:o&&typeof o=="object"&&(s=o.code||""),n.status===401||typeof s=="string"&&s.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,n.status,o),localStorage.removeItem("mrpilot_token"),s==="auth.session_revoked")Ze();else{const u=s==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xe(u),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}const r=new Error("biz_403");throw r.detail=o,r}if(!n.ok)throw new Error("fetch failed");return await n.json()}async function Cn(e,n){const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Qe()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.clone().json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Ze();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xe(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return null}return a}return a}async function Tn(e,n){try{const a=await fetch(e,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json",...Qe()},body:JSON.stringify(n)});if(a.status===401||a.status===403){const s=await a.json().catch(()=>({})),i=s&&s.detail;let r="";if(typeof i=="string"?r=i:i&&typeof i=="object"&&(r=i.code||""),a.status===401||typeof r=="string"&&r.indexOf("auth.")>=0){if(console.warn("[auth-fail-redirect]",e,a.status,i),localStorage.removeItem("mrpilot_token"),r==="auth.session_revoked")Ze();else{const l=r==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(Xe(l),"error"),setTimeout(()=>{window.location.href="/"},1500)}return{ok:!1}}return{ok:!1,status:a.status,detail:i}}const o=await a.json().catch(()=>({}));return{ok:a.ok&&o.ok!==!1,...o}}catch(a){return{ok:!1,error:String(a)}}}window.apiGet=Sn;window.apiPost=Cn;window.t=Xe;window.escapeHtml=Bn;window.svgIcon=Ln;window._showSessionRevokedModal=Ze;window._wsHeader=Qe;window.apiPut=Tn;window.getMaxFiles=xn;window.getMaxPagesPerFile=En;window.getMaxMbPerFile=In;function gt(e){document.body.classList.add("lang-switching");const n=document.getElementById("lang-switching-overlay");n&&n.classList.add("show"),currentLang=e,window._currentLang=e,localStorage.setItem("mrpilot_lang",e),document.documentElement.lang=e;try{const i=localStorage.getItem("mrpilot_token");if(i){if(window.__langSyncCtrl)try{window.__langSyncCtrl.abort()}catch{}window.__langSyncTimer&&clearTimeout(window.__langSyncTimer),window.__langSyncTimer=setTimeout(function(){window.__langSyncCtrl=new AbortController,fetch("/api/me/lang",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+i},body:JSON.stringify({lang:e}),signal:window.__langSyncCtrl.signal}).catch(function(){})},200)}}catch{}document.querySelectorAll("[data-i18n]").forEach(i=>{const r=i.getAttribute("data-i18n");I18N[e]&&I18N[e][r]&&(i.textContent=I18N[e][r])}),document.querySelectorAll("[data-i18n-placeholder]").forEach(i=>{const r=i.getAttribute("data-i18n-placeholder");I18N[e]&&I18N[e][r]&&(i.placeholder=I18N[e][r])});const a=document.getElementById("lang-current");a&&(a.textContent=I18N[e]["lang-name"]),document.querySelectorAll("#lang-dropdown .dd-item").forEach(i=>{i.classList.toggle("active",i.dataset.lang===e)});const o=document.getElementById("general-lang");o&&(o.value=e);const s=document.getElementById("col-conf-th");s&&s.setAttribute("data-tip",t("col-conf-tip")),_userInfo&&typeof window.renderInfoBar=="function"&&window.renderInfoBar(),_quota&&yt(),window.renderFileList&&window.renderFileList(),window.renderResults&&window.renderResults(),currentRoute==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings();try{typeof renderErpEndpointsList=="function"&&window._erpEndpoints&&window._erpEndpoints.length&&renderErpEndpointsList()}catch{}try{typeof loadErpLogs=="function"&&(currentRoute==="automation"||currentRoute==="integrations")&&(loadErpLogs(),typeof loadErpTodayStats=="function"&&loadErpTodayStats())}catch{}try{typeof window._rerenderEmailIngest=="function"&&currentRoute==="automation"&&window._rerenderEmailIngest()}catch{}try{typeof window._rerenderArchiveAll=="function"&&window._rerenderArchiveAll()}catch{}try{typeof window._rerenderExceptions=="function"&&currentRoute==="exceptions"&&window._rerenderExceptions()}catch{}try{typeof window._rerenderNotifications=="function"&&currentRoute==="automation"&&window._rerenderNotifications()}catch{}try{typeof renderHistoryList=="function"&&currentRoute==="history"&&renderHistoryList()}catch{}try{currentRoute==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage()}catch{}try{currentRoute==="settings"&&typeof loadTeamList=="function"&&document.querySelector('.settings-tab[data-tab="team"].active')&&loadTeamList()}catch{}if(Array.isArray(window.__i18nSubs))for(const i of window.__i18nSubs)try{i.fn()}catch(r){console.warn('[i18n] sub "'+i.name+'" rerender failed:',r)}requestAnimationFrame(()=>{requestAnimationFrame(()=>{document.body.classList.remove("lang-switching")})}),setTimeout(()=>{const i=document.getElementById("lang-switching-overlay");i&&i.classList.remove("show")},400)}function $n(e,n){const a=document.getElementById(e);if(!a)return;a.querySelector(".dd-btn").addEventListener("click",s=>{s.stopPropagation(),document.querySelectorAll(".dropdown.open").forEach(i=>{i!==a&&i.classList.remove("open")}),a.classList.toggle("open")}),a.querySelectorAll(".dd-item").forEach(s=>{s.addEventListener("click",i=>{i.stopPropagation(),a.classList.remove("open"),n(s)})})}document.addEventListener("click",()=>{document.querySelectorAll(".dropdown.open").forEach(e=>e.classList.remove("open"))});$n("lang-dropdown",e=>gt(e.dataset.lang));const Pt=["ocr","dashboard","history","integration","integrations","templates","api-keys","settings","exceptions","clients","vouchers","sales-invoices","receivables","reconcile","cloud","test-center"];function Dt(e){Pt.includes(e)||(e="ocr"),currentRoute=e,typeof window.expandNavGroupForRoute=="function"&&window.expandNavGroupForRoute(e),document.querySelectorAll(".page").forEach(o=>o.classList.remove("active"));const n="page-"+e,a=document.getElementById(n);if(a&&a.classList.add("active"),document.querySelectorAll(".nav-item").forEach(o=>{o.classList.toggle("active",o.dataset.route===e)}),location.hash!=="#/"+e&&history.replaceState(null,"","#/"+e),window.innerWidth<=768&&document.body.classList.remove("sidebar-open"),e==="settings"&&typeof window.renderSettings=="function"&&window.renderSettings(),e==="history"&&typeof window.loadHistoryPage=="function"&&window.loadHistoryPage(),e==="clients"&&typeof window.loadClientsPage=="function"&&window.loadClientsPage(),e==="exceptions"&&typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),e==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage(),e==="test-center"&&typeof window.loadTestCenterPage=="function"&&window.loadTestCenterPage(),e==="dashboard"&&typeof window.loadDashboard=="function"&&window.loadDashboard(),e==="integrations"){if(typeof loadErpLogs=="function")try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}function qt(){const e=document.getElementById("brand-workspace");if(!e||!_userInfo)return;const n=_userInfo;function a(i){return!i||typeof i!="string"||(i=i.trim(),!i)?null:i.includes("@")&&i.indexOf("@")>0&&i.indexOf(".")>i.indexOf("@")?i.split("@")[0]:i}const o=[n.company_name,n.company,n.tenant_name,n.organization,n.org_name,n.name,n.full_name,n.display_name,n.username,n.email];let s=null;for(const i of o){const r=a(i);if(r){s=r;break}}s||(s=t("brand-workspace-fallback")||"我的工作台"),e.textContent=s,e.title=s,e.removeAttribute("data-i18n"),!n.company_name&&!n.company&&console.debug("[Pearnly] brand-workspace fallback to:",s,"· _userInfo fields:",Object.keys(n))}function yt(){_quota&&(document.getElementById("upload-hint").textContent=t("upload-hint",{pages:getMaxPagesPerFile(),mb:getMaxMbPerFile(),files:getMaxFiles()}))}async function Rt(){try{const[e,n,a,o]=await Promise.all([apiGet("/api/me"),apiGet("/api/ocr/quota"),fetch("/api/contact").then(s=>s.json()).catch(()=>null),apiGet("/api/me/plan").catch(()=>null)]);if(!e||!n)return;_userInfo=e;try{window._userInfo=e}catch{}if(window.PEARNLY_ADMIN_LAYOUT){_quota=n,_contact=a,o&&(window._planState=o),window.PEARNLY_ADMIN_MODE=!0;try{window._userInfoForAdmin=e}catch{}return}try{const s=location.pathname==="/admin"||location.pathname.startsWith("/admin/"),i=!!e.is_super_admin;if(s&&!i){window.location.replace("/home");return}if(!s&&i){window.location.replace("/admin/cost");return}window.PEARNLY_ADMIN_MODE=s}catch{window.PEARNLY_ADMIN_MODE=!1}_quota=n,_contact=a,o&&(window._planState=o),qt(),typeof window.renderInfoBar=="function"&&window.renderInfoBar(),typeof window.renderQuotaBanner=="function"&&window.renderQuotaBanner(),typeof window.applySidebarVisibility=="function"&&window.applySidebarVisibility();try{typeof applyRoleVisibility=="function"&&applyRoleVisibility(),typeof renderAvatarMenu=="function"&&renderAvatarMenu(e)}catch(s){console.error("[nav-ia phase1] render avatar menu",s)}yt(),typeof window.updateStartButton=="function"&&window.updateStartButton();try{const s=sessionStorage.getItem("pearnly_must_change_pw")==="1",i=e&&e.role==="member"&&!e.is_super_admin;if(s&&i){typeof window.showForceChangePasswordModal=="function"&&window.showForceChangePasswordModal();return}if(s&&!i)try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}}catch(s){console.error("force-pw init",s)}try{typeof window.maybeShowOnboarding=="function"&&window.maybeShowOnboarding(e)}catch(s){console.error("onboarding init",s)}try{typeof window.fillSettingsForms=="function"&&window.fillSettingsForms(e)}catch(s){console.error("settings forms init",s)}}catch(e){console.error(e)}}function Mn(){let e=document.getElementById("offline-banner");e||(e=document.createElement("div"),e.id="offline-banner",e.className="offline-banner",e.style.display="none",document.body.insertBefore(e,document.body.firstChild));function n(){navigator.onLine===!1?(e.innerHTML=svgIcon("wifiOff",14)+"<span>"+escapeHtml(t("offline-banner"))+"</span>",e.classList.remove("is-online"),e.classList.add("is-offline"),e.style.display="flex"):e.classList.contains("is-offline")?(e.innerHTML=svgIcon("wifiOn",14)+"<span>"+escapeHtml(t("online-reconnected"))+"</span>",e.classList.remove("is-offline"),e.classList.add("is-online"),setTimeout(()=>{e.style.display="none",e.classList.remove("is-online")},2e3)):e.style.display="none"}window.addEventListener("online",n),window.addEventListener("offline",n),n()}window.applyLang=gt;window.routeTo=Dt;window.loadAll=Rt;window.renderBrandWorkspace=qt;window.updateUploadHint=yt;window.installNetworkBanner=Mn;try{gt(currentLang)}catch(e){console.warn("[boot] applyLang failed",e)}try{const e=(location.hash||"#/ocr").replace(/^#\//,"");Dt(Pt.includes(e)?e:"ocr")}catch(e){console.warn("[boot] routeTo failed",e)}setTimeout(()=>{currentRoute==="reconcile"&&typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()},0);Rt();const Nt="mrpilot_sidebar_collapsed";localStorage.getItem(Nt)==="1"&&document.body.classList.add("sidebar-collapsed");document.getElementById("sidebar-toggle").addEventListener("click",()=>{window.innerWidth<=768?document.body.classList.toggle("sidebar-open"):(document.body.classList.toggle("sidebar-collapsed"),localStorage.setItem(Nt,document.body.classList.contains("sidebar-collapsed")?"1":"0"))});document.getElementById("topbar-hamburger")?.addEventListener("click",()=>{document.body.classList.toggle("sidebar-open")});document.getElementById("sidebar-overlay")?.addEventListener("click",()=>{document.body.classList.remove("sidebar-open")});window.addEventListener("hashchange",()=>{const e=(location.hash||"#/ocr").replace(/^#\//,"");routeTo(e)});document.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{if(e.dataset.locked==="1"){showToast(t("feature-coming-soon"),"info");return}routeTo(e.dataset.route)})});(function(){function e(a){const o=document.querySelectorAll("#page-integrations .int-top-tab"),s=document.querySelectorAll("#page-integrations .int-top-panel");if(o.forEach(i=>{const r=i.dataset.intTopTab;i.classList.toggle("active",r===a)}),s.forEach(i=>{const r=i.dataset.intTopPanel;i.classList.toggle("active",r===a)}),a==="logs"&&typeof loadErpLogs=="function"){try{loadErpLogs()}catch{}if(typeof loadErpTodayStats=="function")try{loadErpTodayStats()}catch{}}}window.activateIntegrationsLogsTab=function(){try{const a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&a.classList.remove("open"),o&&o.classList.remove("open"),typeof window.closeIntegrationDrawer=="function"&&window.closeIntegrationDrawer()}catch{}if(typeof window.navigateTo=="function")try{window.navigateTo("integrations")}catch{}else try{location.hash="#/integrations"}catch{}e("logs");try{const a=document.getElementById("page-integrations");a&&a.scrollIntoView({block:"start",behavior:"smooth"})}catch{}},document.addEventListener("click",function(a){const o=a.target.closest("#page-integrations .int-top-tab");if(o){const i=o.dataset.intTopTab;i&&e(i);return}a.target.closest('[data-int-action="view-logs"], .int-btn-view-logs')&&(a.preventDefault(),a.stopPropagation(),window.activateIntegrationsLogsTab())});function n(){const a=(location.hash||"").toLowerCase();a.includes("integrations")&&a.includes("tab=logs")&&setTimeout(()=>e("logs"),50)}window.addEventListener("hashchange",n),document.readyState==="complete"||document.readyState==="interactive"?n():document.addEventListener("DOMContentLoaded",n)})();(function(){function e(){const a=document.getElementById("int-drawer-body");if(!a)return;const o=document.querySelector(".auto-content");o&&Array.from(a.querySelectorAll(".auto-panel")).forEach(function(s){s.style.display="",o.appendChild(s)})}window.openIntegrationDrawer=function(a,o){const s=document.getElementById("int-drawer"),i=document.getElementById("int-drawer-overlay"),r=document.getElementById("int-drawer-title"),u=document.getElementById("int-drawer-body");if(!s||!u)return;e(),s.dataset.currentTab=a||"",r&&(r.textContent=o||""),u.innerHTML="";var l={line:"linebot",folder:"folder",email:"email",alert:"alert",erp:"erp",bank:"bank"},d=l[a]||a;const c=document.querySelector('.auto-panel[data-auto-panel="'+d+'"]');c?(c.style.display="block",u.appendChild(c)):u.innerHTML='<div style="padding:20px;color:var(--ink-3);font-size:13px;">面板未找到</div>',s.classList.add("open"),i&&(i.style.display="block"),document.body.style.overflow="hidden";var p={line:window._loadLineBotPanel,folder:window._loadFolderWatcherPanel,email:window._loadEmailIngestPanel,alert:window._loadNotificationsPanel,bank:window._loadBankReconPanel};if(p[a])try{p[a]()}catch(f){console.warn("[int-drawer] loader error",f)}else if(a==="erp")try{typeof loadErpEndpoints=="function"&&loadErpEndpoints(),typeof loadErpLogs=="function"&&loadErpLogs()}catch(f){console.warn("[int-drawer] ERP load error",f)}},window.closeIntegrationDrawer=function(){e();var a=document.getElementById("int-drawer"),o=document.getElementById("int-drawer-overlay");a&&(a.classList.remove("open"),a.dataset.currentTab=""),o&&(o.style.display="none"),document.body.style.overflow=""};function n(){var a=document.getElementById("int-drawer-close"),o=document.getElementById("int-drawer-overlay");a&&a.addEventListener("click",window.closeIntegrationDrawer),o&&o.addEventListener("click",window.closeIntegrationDrawer),document.addEventListener("keydown",function(s){s.key==="Escape"&&window.closeIntegrationDrawer()})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.querySelectorAll(".settings-tab");if(!a.length){setTimeout(n,200);return}a.forEach(s=>{s.addEventListener("click",()=>switchSettingsTab(s.dataset.tab))});let o=null;try{o=localStorage.getItem("mrpilot_settings_tab")}catch{}if(o){const s=document.querySelector(`.settings-tab[data-tab="${o}"]`);if(s&&s.style.display!=="none"){switchSettingsTab(o);return}}switchSettingsTab("profile")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){function n(){const a=document.getElementById("btn-save-profile"),o=document.getElementById("btn-save-company");if(!a&&!o){setTimeout(n,200);return}a&&a.addEventListener("click",saveProfile),o&&o.addEventListener("click",saveCompany)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();let Ue=null;function Hn(){ut(),Ue=setInterval(async()=>{try{(await fetch("/api/health").then(n=>n.json())).ocr_ready&&ut()}catch{}},1e4)}function ut(){Ue&&(clearInterval(Ue),Ue=null)}window.startEnginePolling=Hn;window.stopEnginePolling=ut;document.getElementById("drawer-body").addEventListener("click",e=>{const n=e.target.closest("[data-rd-action]");if(n){const s=n.dataset.rdAction,i=n.dataset.rdSide;s==="verify"?callRdVerify(i):s==="sync"&&callRdSync(i);return}if(e.target.closest(".rd-btn-locked")){showToast(t("feature-contact-us"),"info");return}const o=e.target.closest("[data-archive-copy]");if(o){const s=o.dataset.archiveCopy;navigator.clipboard?.writeText(s).then(()=>{showToast(t("copied"),"success")}).catch(()=>{showToast(t("copy-failed"),"error")})}});document.getElementById("drawer-close").addEventListener("click",()=>closeDrawer());document.getElementById("drawer-mask").addEventListener("click",()=>closeDrawer());document.addEventListener("keydown",e=>{e.key==="Escape"&&document.getElementById("drawer").classList.contains("show")&&closeDrawer()});document.addEventListener("click",e=>{e.target.closest("[data-upgrade]")&&e.preventDefault()});const Tt=document.getElementById("btn-custom-template");Tt&&Tt.addEventListener("click",()=>{showToast(t("cs-coming-soon"),"info")});document.addEventListener("DOMContentLoaded",()=>{installNetworkBanner()});window.pearnlyConfirm=function(e,n){return new Promise(function(a){const o=document.getElementById("pearnly-confirm-modal"),s=document.getElementById("pearnly-confirm-title"),i=document.getElementById("pearnly-confirm-msg"),r=document.getElementById("pearnly-confirm-ok"),u=document.getElementById("pearnly-confirm-cancel"),l=document.getElementById("pearnly-confirm-close");if(!o||!i||!r||!u){a(window.confirm(e));return}s&&(s.textContent=n||(typeof t=="function"?t("confirm-default-title"):"Please confirm")),i.textContent=e||"",o.style.display="flex";function d(b){o.style.display="none",r.removeEventListener("click",c),u.removeEventListener("click",p),l&&l.removeEventListener("click",p),o.removeEventListener("click",f),document.removeEventListener("keydown",m),a(b)}function c(){d(!0)}function p(){d(!1)}function f(b){b.target===o&&d(!1)}function m(b){b.key==="Escape"?d(!1):b.key==="Enter"&&d(!0)}r.addEventListener("click",c),u.addEventListener("click",p),l&&l.addEventListener("click",p),o.addEventListener("click",f),document.addEventListener("keydown",m),setTimeout(function(){try{u.focus()}catch{}},50)})};const An=`
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

`,jn=`        <!-- ── 销项税对账面板(v118.32.0 · 屏 A) ── -->
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


`;(function(){const e=document.getElementById("page-reconcile");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=An+jn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=document.getElementById("page-integrations");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();const Pn=`
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

`,Dn=`                    <!-- Tab: 邮箱抓取 (v0.17 · M6 · v93 在 Vultr 复活) -->
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
`;(function(){const e=document.getElementById("page-automation");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=Pn+Dn,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e={"page-integration":`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();function qn(e,n){const a=document.getElementById("alert-"+e);a&&(document.getElementById("alert-"+e+"-text").textContent=n,a.classList.add("show"))}function Rn(){["info","warn","error"].forEach(e=>{document.getElementById("alert-"+e).classList.remove("show")})}function Nn(e,n){if(e==null)return n||"操作失败";if(typeof e=="string")return e;if(Array.isArray(e)){const a=e[0]||{};return a.msg?a.msg:n||"请求格式错误"}if(typeof e=="object"){if(e.code){const a="err."+e.code;try{const o=t(a,e);if(o&&o!==a)return o}catch(o){console.warn("[i18n] t() failed for key:",a,o)}return e.code}if(e.message)return e.message;if(e.error)return e.error;if(e.detail&&typeof e.detail=="string")return e.detail;try{return JSON.stringify(e).slice(0,160)}catch{}}return n||String(e)}function Fn(e){if(!e)return"";const n=String(e);return/ECONNREFUSED|Connection refused/i.test(n)?"连接被拒绝 · ERP 地址可能错了,或服务没启动":/listing fetch failed|wait_for_selector/i.test(n)?"拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试":/ETIMEDOUT|timeout/i.test(n)?"连接超时 · MR.ERP 响应慢 · 稍后再试":/ENOTFOUND|getaddrinfo/i.test(n)?"域名解析失败 · ERP 地址拼错了":/certificate|SSL/i.test(n)?"SSL 证书问题 · ERP 站点证书异常":/401|Unauthorized/i.test(n)?"HTTP 401 · 认证失败,检查 Token 是否正确":/403|Forbidden/i.test(n)?"HTTP 403 · 权限不足,ERP 拒绝访问":/404|Not Found/i.test(n)?"HTTP 404 · URL 路径不存在":/^5\d\d/.test(n)||/500|502|503|504/.test(n)?"ERP 服务器错误 · 不是你的问题,等会儿再试":n}function zn(e,n,a){let o=document.getElementById("mp-toast-wrap");o||(o=document.createElement("div"),o.id="mp-toast-wrap",document.body.appendChild(o)),n=n||"success",n==="ok"&&(n="success"),n==="warning"&&(n="warn"),n==="danger"&&(n="error");const s={success:'<path d="M3 8l3 3 7-7"/>',error:'<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',warn:'<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',info:'<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',loading:'<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>'},i=document.createElement("div");i.className="mp-toast "+n,i.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${s[n]||s.success}
        </svg>
        <span>${escapeHtml(e)}</span>
    `,o.appendChild(i),requestAnimationFrame(()=>i.classList.add("show"));const r=typeof a=="number"?a:2500;let u=null;const l=()=>{u&&(clearTimeout(u),u=null),i.classList.remove("show"),setTimeout(()=>{try{i.remove()}catch{}},300)};return r>0&&(u=setTimeout(l,r)),l}window.showAlert=qn;window.hideAlerts=Rn;window._humanizeBackendError=Nn;window.humanizeError=Fn;window.showToast=zn;function On(e,n){return n=n||{},new Promise(a=>{const o=document.getElementById("confirm-modal"),s=document.getElementById("confirm-modal-body"),i=document.getElementById("confirm-modal-ok"),r=document.getElementById("confirm-modal-cancel"),u=document.getElementById("confirm-modal-close"),l=document.getElementById("confirm-modal-title");if(!o||!s||!i||!r){a(!1);return}l.textContent=n.title||t("confirm-default-title");const d=n.promptInput?"cm_in_"+Date.now():null;if(n.promptInput){const m=(e||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"),b=(n.placeholder||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");s.innerHTML=`
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${m}</div>
                <input type="text" id="${d}" placeholder="${b}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `}else s.textContent=e||"";i.className=n.danger?"btn btn-danger":"btn btn-primary",i.textContent=n.okText||t("confirm-ok"),r.textContent=n.cancelText||t("confirm-cancel"),r.style.display=n.hideCancel?"none":"",o.style.display="flex";const c=m=>{o.style.display="none",i.onclick=null,r.onclick=null,u.onclick=null,o.onclick=null,document.removeEventListener("keydown",f),n.promptInput&&(s.innerHTML=""),r.style.display="",a(m)},p=()=>{const m=d?document.getElementById(d):null;return m?m.value:""},f=m=>{m.key==="Escape"?c(n.promptInput?null:!1):m.key==="Enter"&&c(n.promptInput?p():!0)};i.onclick=()=>c(n.promptInput?p():!0),r.onclick=()=>c(n.promptInput?null:!1),u.onclick=()=>c(n.promptInput?null:!1),o.onclick=m=>{m.target===o&&c(n.promptInput?null:!1)},document.addEventListener("keydown",f),setTimeout(()=>{if(n.promptInput){const m=document.getElementById(d);m&&m.focus()}else i.focus()},50)})}window.showConfirm=On;function Vn(e){if(e){try{if(typeof shouldHideMoney=="function"&&shouldHideMoney(_userInfo)&&["team","api","plan","company"].indexOf(e)>=0){e="profile";try{localStorage.setItem("mrpilot_settings_tab","profile")}catch{}}}catch{}document.querySelectorAll(".settings-tab").forEach(n=>{n.classList.toggle("active",n.dataset.tab===e)}),document.querySelectorAll(".settings-pane").forEach(n=>{n.classList.toggle("active",n.dataset.pane===e)});try{localStorage.setItem("mrpilot_settings_tab",e)}catch{}try{e==="about"&&typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),e==="notifications"&&typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings(),e==="team"&&loadTeamList(),e==="learned"&&typeof window.loadLearnedRules=="function"&&window.loadLearnedRules(),e==="plan"&&typeof ft=="function"&&ft()}catch(n){console.warn("settings tab side effect failed:",n)}}}function Un(e){if(!e)return;const n=(a,o)=>{const s=document.getElementById(a);s&&(s.value=o||"")};n("profile-username",e.username||""),n("profile-email",e.username||""),n("profile-fullname",e.full_name||""),n("profile-phone",e.phone||""),n("profile-country",e.country||"TH"),n("profile-line",e.line_id||""),n("company-name",e.company_name||""),n("company-volume",e.monthly_volume||""),n("company-role",e.user_role||e.role_self||"")}async function Gn(){const e=document.getElementById("btn-save-profile"),n=document.getElementById("profile-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={full_name:(document.getElementById("profile-fullname")||{}).value||"",phone:(document.getElementById("profile-phone")||{}).value||"",country:(document.getElementById("profile-country")||{}).value||"TH",line_id:(document.getElementById("profile-line")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}async function Kn(){const e=document.getElementById("btn-save-company"),n=document.getElementById("company-save-msg");if(!e)return;const a=e.innerHTML;e.disabled=!0,e.innerHTML=`<span>${t("msg-saving")||"保存中..."}</span>`,n&&(n.textContent="",n.classList.remove("error"));try{const o={company_name:(document.getElementById("company-name")||{}).value||"",monthly_volume:(document.getElementById("company-volume")||{}).value||"",role:(document.getElementById("company-role")||{}).value||""},s=await apiPut("/api/me/profile",o);if(s&&s.ok){n&&(n.textContent=t("msg-saved")||"已保存");try{const i=await apiGet("/api/me");_userInfo=i;try{window._userInfo=i}catch{}renderBrandWorkspace()}catch{}}else throw new Error("save failed")}catch{n&&(n.textContent=t("msg-save-failed")||"保存失败",n.classList.add("error"))}finally{e.disabled=!1,e.innerHTML=a,setTimeout(()=>{n&&(n.textContent="")},3e3)}}function ft(){if(!_userInfo)return;typeof window.loadAboutPanel=="function"&&window.loadAboutPanel(),typeof window.loadPrefsSettings=="function"&&window.loadPrefsSettings();const e=document.getElementById("settings-info");if(!e)return;const n=_userInfo;if(n.is_super_admin){e.innerHTML=`
            <table style="width:100%; font-size:13px; border-collapse: collapse;">
                <tr><td style="color:#a0aec0; padding:8px 0; width:120px;">${t("settings-username")}</td><td style="padding:8px 0;">${escapeHtml(n.username)}</td></tr>
                <tr><td style="color:#a0aec0; padding:8px 0;">${t("settings-role")}</td><td style="padding:8px 0;"><strong style="color:#d97706;">🛡️ ${escapeHtml(t("settings-role-super-admin"))}</strong></td></tr>
            </table>
        `;const o=document.getElementById("api-key-card");o&&(o.style.display="");return}Jn(n,e);const a=document.getElementById("api-key-card");if(a){const o=tt==="byo_api"||_userInfo&&_userInfo.is_super_admin;a.style.display=o?"":"none"}}function Jn(e,n){const a=escapeHtml(e.username||e.email||"");n.innerHTML=`
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
    `}window.switchSettingsTab=Vn;window.fillSettingsForms=Un;window.saveProfile=Gn;window.saveCompany=Kn;window.renderSettings=ft;function et(e){return e=e||_userInfo,!!(e&&e.is_super_admin)}function bt(e){return e=e||_userInfo,!!e&&(e.role==="owner"||et(e))}function Ft(e){return e=e||_userInfo,!!e&&e.role==="member"&&!et(e)}function Yn(e){return e=e||_userInfo,!!e&&(e.effective_plan==="trial"||e.plan==="trial")&&!et(e)}function zt(e){return e=e||_userInfo,!!e&&e.tenant_type==="byo_api"}function Ot(e){return Ft(e)}function Wn(e){return bt(e)}function Xn(e){return bt(e)&&zt(e)}window.isMoneyHidden=Ot;window.isSuperAdmin=et;window.isOwner=bt;window.isEmployee=Ft;window.isTrial=Yn;window.isLifetime=zt;window.shouldHideMoney=Ot;window.canManageTeam=Wn;window.canManageApiKey=Xn;function Zn(){const e=document.getElementById("quota-banner");if(!e)return;if(!_userInfo){e.style.display="none";return}if(_userInfo.is_super_admin||_userInfo.tenant_type==="admin"||_userInfo.tenant_type==="byo_api"){e.style.display="none";return}let n=0,a=0;if(_userInfo.plan==="free"&&_quota&&_quota.ip_daily_limit)n=_quota.ip_used_today||0,a=_quota.ip_daily_limit;else if(_userInfo.tenant_quota!=null&&_userInfo.tenant_quota>0)n=_userInfo.tenant_used||0,a=_userInfo.tenant_quota;else if(_userInfo.monthly_quota&&_userInfo.monthly_quota>0)n=_userInfo.used_this_month||0,a=_userInfo.monthly_quota;else{e.style.display="none";return}if(a<=0){e.style.display="none";return}const o=Math.max(0,a-n),s=n/a*100,i="quota_banner_dismiss_"+new Date().toISOString().slice(0,10);if(localStorage.getItem(i)){e.style.display="none";return}let r,u;if(o===0)r="danger",u=t("quota-banner-exhausted");else if(s>=90)r="danger",u=t("quota-banner-very-low",{n:o});else if(s>=70)r="warn",u=t("quota-banner-low",{n:o});else{e.style.display="none";return}e.className="quota-banner "+r,e.innerHTML=`
        <span class="quota-banner-icon">${svgIcon("alert",18)}</span>
        <span class="quota-banner-msg">${escapeHtml(u)}</span>
        <button type="button" class="quota-banner-close" aria-label="dismiss" title="${escapeHtml(t("quota-banner-dismiss"))}">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
        </button>
    `,e.style.display="flex";const l=e.querySelector(".quota-banner-close");l&&l.addEventListener("click",()=>{localStorage.setItem(i,"1"),e.style.display="none"})}function Qn(){const e=_userInfo;if(!e)return;const n=shouldHideMoney(e),a=canManageTeam(e),o=canManageApiKey(e),s=document.querySelector('.nav-item[data-route="templates"]');s&&(s.classList.remove("locked-for-plan"),s.removeAttribute("data-locked-target"));const i=document.querySelector('.nav-item[data-route="api-keys"]');i&&(i.classList.remove("locked-for-plan"),i.removeAttribute("data-locked-target"));const r=document.getElementById("btn-custom-template");r&&(r.style.display="",r.classList.remove("locked-for-plan"));const u=document.querySelector('.settings-tab[data-tab="team"]');u&&(u.style.display=a?"":"none");const l=document.querySelector('.settings-panel[data-settings-panel="team"]');l&&(l.dataset.permHidden=a?"0":"1");const d=document.querySelector('.settings-tab[data-tab="api"]');d&&(d.style.display=o||isSuperAdmin(e)?"":"none");const c=document.querySelector('.settings-tab[data-tab="plan"]');c&&(c.style.display=n?"none":"");const p=document.querySelector('.settings-tab[data-tab="company"]');p&&(p.style.display=n?"none":"");const f=document.getElementById("info-bar");f&&(f.style.display=n?"none":"");const m=document.getElementById("trial-banner");m&&n&&(m.style.display="none");const b=document.getElementById("plan-banner");b&&n&&(b.style.display="none",document.body.classList.remove("has-plan-banner")),document.querySelectorAll("[data-upgrade-cta], .btn-upgrade, .topbar-upgrade").forEach(M=>{M.style.display="none"}),document.body.classList.toggle("role-employee",isEmployee(e)),document.body.classList.toggle("role-owner",isOwner(e)),document.body.classList.toggle("role-super",isSuperAdmin(e));try{const M=document.querySelector(".settings-tab.active");M&&M.style.display==="none"&&(typeof window.switchSettingsTab=="function"?window.switchSettingsTab("profile"):typeof switchSettingsTab=="function"&&switchSettingsTab("profile"))}catch(M){console.warn("[v118.12.3] failed to fix active tab:",M)}if(window.PEARNLY_ADMIN_MODE){const M=document.getElementById("admin-mode-banner");M&&(M.style.display="flex"),document.querySelectorAll(".nav-item").forEach(y=>{y.classList.contains("nav-admin-only")||(y.style.display="none")}),document.querySelectorAll(".nav-group").forEach(y=>{y.classList.contains("nav-group-admin-only")||(y.style.display="none")});const I=document.getElementById("client-switcher");I&&(I.style.display="none"),document.body.classList.add("admin-mode");const x=["profile","security","notifications","about"];document.querySelectorAll(".settings-tab").forEach(y=>{const $=y.dataset.tab;$&&!x.includes($)&&(y.style.display="none")}),document.querySelectorAll(".settings-pane").forEach(y=>{const $=y.dataset.pane;$&&!x.includes($)&&(y.style.display="none")}),document.querySelectorAll(".settings-nav-group").forEach(y=>{const $=y.querySelectorAll(".settings-tab");Array.from($).some(F=>F.style.display!=="none")||(y.style.display="none")})}}function ea(){const e=_userInfo,n=document.getElementById("info-bar");if(!e||shouldHideMoney(e)){n&&(n.innerHTML="");return}let a="";const o=e.tenant_type;if(o==="byo_api")e.has_own_gemini_key?a=`
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
        `;else{const s=e.tenant_used!=null?e.tenant_used:e.used_this_month||0,i=e.tenant_quota!=null&&e.tenant_quota>0?e.tenant_quota:e.monthly_quota||0,r=i>0?Math.min(100,s/i*100):0;let u="";r>=95?u="danger":r>=80&&(u="warn"),i>0?a=`
                <div class="info-chip">
                    <span class="chip-label">${escapeHtml(t("info-monthly"))}</span>
                    <span class="chip-value">${s} / ${i}</span>
                    <div class="mini-bar"><div class="mini-bar-fill ${u}" style="width:${r}%"></div></div>
                </div>
            `:a=""}n&&(n.innerHTML=a)}window.renderQuotaBanner=Zn;window.applySidebarVisibility=Qn;window.renderInfoBar=ea;async function Vt(e,n){try{const a=await fetch(e,{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(n)});if(a.status===401){localStorage.removeItem("mrpilot_token");const o=await a.json().catch(()=>({}));return(typeof o.detail=="string"?o.detail:o.detail&&o.detail.code||"")==="auth.session_revoked"?(_showSessionRevokedModal(),null):(window.location.href="/",null)}return await a.json()}catch{return{ok:!1,error:"network"}}}function Ut(e){return{invalid_format:"rd-err-format",not_found:"rd-err-not-found",rd_unreachable:"rd-err-unreachable",parse_error:"rd-err-unknown",network:"rd-err-unreachable"}[e]||"rd-err-unknown"}function Ke(e){const n=document.querySelector(`[data-field="${e}"]`);return n?(n.value||"").trim():""}function Se(e,n,a){const o=document.querySelector(`[data-rd-status="${e}"]`);o&&(o.innerHTML=n,o.className="rd-status"+(a?" "+a:""))}async function ta(e){const a=Ke(e==="seller"?"seller_tax":"buyer_tax");Se(e,t("rd-verifying"),"loading");const o=await Vt("/api/rd/verify",{tax_id:a});if(!o)return;if(!o.ok){Se(e,t(Ut(o.error)),"error");return}o.data&&o.data.valid?Se(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"):Se(e,t("rd-status-invalid"),"invalid")}async function na(e){const a=Ke(e==="seller"?"seller_tax":"buyer_tax");Se(e,t("rd-syncing"),"loading");const o=await Vt("/api/rd/lookup",{tax_id:a,branch:0});if(o){if(!o.ok){Se(e,t(Ut(o.error)),"error");return}Se(e,`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8l3 3 7-7"/></svg> ${escapeHtml(t("rd-status-valid"))}`,"valid"),aa(e,o.data)}}function aa(e,n){const a=e==="seller"?"seller_name":"buyer_name",o=e==="seller"?"seller_addr":"buyer_addr",s=Ke(a),i=Ke(o),r=[];n.name&&n.name!==s&&r.push({field:a,label:t("rd-field-name"),current:s,official:n.name}),n.address&&n.address!==i&&r.push({field:o,label:t("rd-field-address"),current:i,official:n.address});const u=[];n.branch_label&&u.push(`<strong>${t("rd-field-branch")}:</strong> ${escapeHtml(n.branch_label)}`),n.post_code&&u.push(`<strong>${t("rd-field-postcode")}:</strong> ${escapeHtml(n.post_code)}`);let l=document.getElementById("rd-sync-modal");if(l||(l=document.createElement("div"),l.id="rd-sync-modal",l.className="rd-modal-mask",document.body.appendChild(l)),r.length===0)l.innerHTML=`
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
                    ${u.length?`<div class="rd-modal-extra">${u.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                </div>
            </div>
        `;else{const p=r.map((f,m)=>`
            <label class="rd-diff-row">
                <input type="checkbox" data-rd-apply data-field="${f.field}" data-value="${escapeHtml(f.official)}" checked>
                <div class="rd-diff-label">${escapeHtml(f.label)}</div>
                <div class="rd-diff-col rd-diff-current">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-current"))}</div>
                    <div class="rd-diff-val">${escapeHtml(f.current||"—")}</div>
                </div>
                <div class="rd-diff-arrow">→</div>
                <div class="rd-diff-col rd-diff-official">
                    <div class="rd-diff-col-label">${escapeHtml(t("rd-modal-official"))}</div>
                    <div class="rd-diff-val">${escapeHtml(f.official)}</div>
                </div>
            </label>
        `).join("");l.innerHTML=`
            <div class="rd-modal">
                <div class="rd-modal-head">
                    <h3>${escapeHtml(t("rd-modal-title"))}</h3>
                    <button class="rd-modal-close" type="button">×</button>
                </div>
                <div class="rd-modal-body">
                    ${p}
                    ${u.length?`<div class="rd-modal-extra">${u.join(" · ")}</div>`:""}
                </div>
                <div class="rd-modal-foot">
                    <button class="rd-modal-btn" type="button" data-rd-modal-close>${escapeHtml(t("rd-modal-cancel"))}</button>
                    <button class="rd-modal-btn primary" type="button" data-rd-modal-apply>${escapeHtml(t("rd-modal-apply"))}</button>
                </div>
            </div>
        `}l.classList.add("show");const d=()=>l.classList.remove("show");l.querySelector(".rd-modal-close").addEventListener("click",d),l.querySelectorAll("[data-rd-modal-close]").forEach(p=>p.addEventListener("click",d)),l.addEventListener("click",p=>{p.target===l&&d()});const c=l.querySelector("[data-rd-modal-apply]");c&&c.addEventListener("click",()=>{const p=_results[_drawerIdx];if(!p){d();return}l.querySelectorAll("[data-rd-apply]:checked").forEach(f=>{const m=f.dataset.field,b=f.dataset.value;p.edits[m]=b,p.merged_fields[m]=b;const M=document.querySelector(`[data-field="${m}"]`);M&&(M.value=b);const I=document.querySelector(`[data-field-wrap="${m}"]`);I&&I.classList.add("edited")}),updateDrawerEditCount(),renderResults(),d()})}window.callRdVerify=ta;window.callRdSync=na;function oa(e){const n={invoice_number:null,date:null,total_amount:null,tax_ids:[],seller_name:"",seller_tax:"",seller_addr:"",buyer_name:"",buyer_tax:"",buyer_addr:"",subtotal:"",vat:"",notes:"",items:[]},a=e.filter(s=>!s.is_duplicate&&!s.is_copy),o=a.length>0?a:e;for(const s of o){const i=s.fields||{};!n.invoice_number&&i.invoice_number&&(n.invoice_number=i.invoice_number),!n.date&&i.date&&(n.date=i.date),!n.total_amount&&i.total_amount&&(n.total_amount=i.total_amount),!n.subtotal&&i.subtotal&&(n.subtotal=i.subtotal),!n.vat&&i.vat&&(n.vat=i.vat),!n.seller_name&&i.seller_name&&(n.seller_name=i.seller_name),!n.seller_tax&&i.seller_tax&&(n.seller_tax=i.seller_tax),!n.seller_addr&&i.seller_addr&&(n.seller_addr=i.seller_addr),!n.buyer_name&&i.buyer_name&&(n.buyer_name=i.buyer_name),!n.buyer_tax&&i.buyer_tax&&(n.buyer_tax=i.buyer_tax),!n.buyer_addr&&i.buyer_addr&&(n.buyer_addr=i.buyer_addr),!n.notes&&i.notes&&(n.notes=i.notes),Array.isArray(i.items)&&i.items.length&&n.items.push(...i.items),Array.isArray(i.tax_ids)&&n.tax_ids.push(...i.tax_ids)}return n.tax_ids=[...new Set(n.tax_ids)],!n.seller_tax&&n.tax_ids[0]&&(n.seller_tax=n.tax_ids[0]),!n.buyer_tax&&n.tax_ids[1]&&(n.buyer_tax=n.tax_ids[1]),n}function sa(e){const n=e.target.dataset.field,a=e.target.value,o=_results[_drawerIdx],s=o.merged_fields[n];a===(s??"")?delete o.edits[n]:(o.edits[n]=a,o.merged_fields[n]=a);const i=document.querySelector(`[data-field-wrap="${n}"]`);i&&i.classList.toggle("edited",o.edits[n]!==void 0),Gt(),renderResults()}function Gt(){const e=_results[_drawerIdx],n=e?Object.keys(e.edits).length:0,a=document.getElementById("drawer-edit-count-sub");a&&(a.textContent=n>0?t("drawer-edit-count",{n}):"")}window.mergeFields=oa;window.onFieldEdit=sa;window.updateDrawerEditCount=Gt;function ia(){document.querySelectorAll(".force-pw-overlay").forEach(a=>a.remove());const e=document.createElement("div");e.className="force-pw-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const a=document.getElementById("force-pw-old");a&&a.focus()},200);const n=e.querySelector("#force-pw-submit");n.addEventListener("click",async()=>{const a=document.getElementById("force-pw-old").value,o=document.getElementById("force-pw-new").value,s=document.getElementById("force-pw-new2").value,i=document.getElementById("force-pw-msg");if(i.textContent="",i.classList.remove("error"),!a||!o){i.textContent=t("msg-fill-all")||"请填写所有字段",i.classList.add("error");return}if(o!==s){i.textContent=t("force-pw-mismatch")||"两次密码不一致",i.classList.add("error");return}if(o.length<8){i.textContent=t("pwd-too-short")||"密码至少 8 位",i.classList.add("error");return}if(/^\d+$/.test(o)){i.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",i.classList.add("error");return}if(!(/[a-zA-Z]/.test(o)&&/\d/.test(o))){i.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",i.classList.add("error");return}if(o===a){i.textContent=t("pwd-same-as-old")||"新密码不能和临时密码相同",i.classList.add("error");return}n.disabled=!0,n.textContent=t("msg-saving")||"保存中...";try{const r=await fetch("/api/me/change_password",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({old_password:a,new_password:o})}),u=await r.json().catch(()=>({}));if(!r.ok){const l=u&&u.detail||"unknown",d={wrong_old_password:t("force-pw-wrong-old")||"临时密码不对",password_too_short:t("pwd-too-short")||"密码至少 8 位",password_too_weak:t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};i.textContent=d[l]||t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续";return}try{sessionStorage.removeItem("pearnly_must_change_pw")}catch{}showToast(t("force-pw-success")||"密码修改成功","success"),e.classList.remove("show"),setTimeout(()=>{e.remove(),location.reload()},600)}catch{i.textContent=t("force-pw-fail")||"修改失败",i.classList.add("error"),n.disabled=!1,n.textContent=t("force-pw-submit")||"修改并继续"}}),e.addEventListener("click",a=>{a.target===e&&a.stopPropagation()})}window.showForceChangePasswordModal=ia;(function(){let e=null,n=null,a=null,o=null;function s(y){return document.getElementById(y)}async function i(){b(),I(),await r()}async function r(){try{const y=localStorage.getItem("mrpilot_token"),$=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+y}});if(!$.ok){M(t("linebot-err-status"));return}const C=await $.json();C.bound?u(C):await l()}catch{M(t("linebot-err-status"))}}function u(y){m(),s("linebot-unbound").style.display="none",s("linebot-bound").style.display="block";const $=s("linebot-status-summary");$&&($.textContent=t("linebot-status-bound"),$.style.background="#D1FAE5",$.style.color="#065F46");const C=s("linebot-bound-name");C&&(C.textContent=y.line_display_name||"(LINE User)");const F=s("linebot-avatar");F&&(y.line_picture_url?(F.src=y.line_picture_url,F.style.display=""):F.style.display="none");const j=s("linebot-bound-since");j&&y.bound_at&&(j.textContent=new Date(y.bound_at).toLocaleString())}async function l(){s("linebot-bound").style.display="none",s("linebot-unbound").style.display="block";const y=s("linebot-status-summary");y&&(y.textContent=t("linebot-status-unbound"),y.style.background="#FEE2E2",y.style.color="#B91C1C"),await d(),f()}async function d(){try{const y=localStorage.getItem("mrpilot_token"),$=await fetch("/api/line/binding-code",{method:"POST",headers:{Authorization:"Bearer "+y}});if(!$.ok){M(t("linebot-err-code"));return}const C=await $.json();a=C.code,o=new Date(C.expires_at).getTime(),c(C)}catch{M(t("linebot-err-code"))}}function c(y){const $=s("linebot-code");$&&($.textContent=y.code);const C=s("linebot-bot-id");C&&(C.textContent=y.bot_basic_id||t("linebot-bot-id-missing"));const F=s("linebot-qr");if(F)if(y.bot_friend_url){const j="https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data="+encodeURIComponent(y.bot_friend_url);F.classList.remove("empty"),F.innerHTML='<img src="'+j+'" alt="LINE Bot QR">'}else F.classList.add("empty"),F.innerHTML="";p()}function p(){e&&clearInterval(e);const y=s("linebot-code-expires");function $(){if(!o)return;const C=o-Date.now();if(C<=0){y&&(y.textContent=t("linebot-code-expired"),y.classList.add("expiring"));const h=s("linebot-code");h&&(h.style.opacity="0.4"),clearInterval(e),e=null;return}const F=Math.floor(C/1e3),j=Math.floor(F/60),_=F%60;y&&(y.textContent=t("linebot-code-expires-in").replace("{m}",j).replace("{s}",String(_).padStart(2,"0")),C<6e4?y.classList.add("expiring"):y.classList.remove("expiring"))}$(),e=setInterval($,1e3)}function f(){m(),n=setInterval(async()=>{try{const y=localStorage.getItem("mrpilot_token"),$=await fetch("/api/line/binding",{headers:{Authorization:"Bearer "+y}});if(!$.ok)return;const C=await $.json();C.bound&&u(C)}catch{}},4e3)}function m(){n&&(clearInterval(n),n=null)}function b(){e&&(clearInterval(e),e=null),m()}function M(y){const $=s("linebot-error");$&&($.textContent=y,$.style.display="block")}function I(){const y=s("linebot-error");y&&(y.style.display="none")}async function x(){if(await showConfirm(t("linebot-unbind-confirm"),{danger:!0}))try{const $=localStorage.getItem("mrpilot_token");if(!(await fetch("/api/line/binding",{method:"DELETE",headers:{Authorization:"Bearer "+$}})).ok){M(t("linebot-err-unbind"));return}await i()}catch{M(t("linebot-err-unbind"))}}document.addEventListener("click",y=>{if(y.target.closest("#linebot-code-refresh")){y.preventDefault(),I(),d();return}if(y.target.closest("#linebot-unbind")){y.preventDefault(),x();return}}),window._loadLineBotPanel=i})();function nt(){const e=document.getElementById("results-card");if(_results.length===0){e.classList.remove("show");return}e.classList.add("show");let n=0;_results.forEach(r=>{const u=parseFloat(r.merged_fields.total_amount);isNaN(u)||(n+=u)}),_selectedFiles&&_selectedFiles.length||_results.length;const a=_results.length,o=n.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2});document.getElementById("results-head-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-value">${a}</span>
            <span class="rh-stat-label">${t("stats-invoices")}</span>
        </div>
        <div class="rh-stat">
            <span class="rh-stat-label">${t("stats-total")}</span>
            <span class="rh-stat-value">฿ ${o}</span>
        </div>
    `;let s=_results.map((r,u)=>({...r,_idx:u}));if(_searchKeyword){const r=_searchKeyword.toLowerCase();s=s.filter(u=>(u.filename||"").toLowerCase().includes(r)||(u.merged_fields.invoice_number||"").toLowerCase().includes(r))}_sortKey&&s.sort((r,u)=>{let l,d;return _sortKey==="filename"?(l=r.filename,d=u.filename):_sortKey==="invoice_no"?(l=r.merged_fields.invoice_number,d=u.merged_fields.invoice_number):_sortKey==="invoice_date"?(l=r.merged_fields.date,d=u.merged_fields.date):_sortKey==="total"?(l=parseFloat(r.merged_fields.total_amount)||0,d=parseFloat(u.merged_fields.total_amount)||0):_sortKey==="confidence"?(l=r.confidence,d=u.confidence):(l="",d=""),l<d?_sortDir==="asc"?-1:1:l>d?_sortDir==="asc"?1:-1:0});const i=document.getElementById("results-tbody");i.innerHTML=s.map((r,u)=>{const l=r.merged_fields,d=`<span class="empty-cell">${t("empty-val")}</span>`,c="conf-tip-"+(r.confidence||"low"),p="conf-"+(r.confidence||"low"),f=t(c),m=t(p);return`
            <tr data-idx="${r._idx}">
                <td class="num">${u+1}</td>
                <td class="fname" title="${escapeHtml(r.filename)}">${escapeHtml(r.filename)}</td>
                <td class="inv">${l.invoice_number?escapeHtml(l.invoice_number):d}</td>
                <td class="date">${l.date?escapeHtml(l.date):d}</td>
                <td class="amount">${l.total_amount?Number(l.total_amount).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):d}</td>
                <td><span class="conf-badge ${r.confidence}" data-tip="${escapeHtml(f)}">${m}</span></td>
            </tr>
        `}).join(""),document.querySelectorAll("#results-table th").forEach(r=>{r.classList.remove("sort-asc","sort-desc"),r.dataset.sort===_sortKey&&r.classList.add("sort-"+_sortDir)}),i.querySelectorAll("tr").forEach(r=>{r.addEventListener("click",()=>{const u=parseInt(r.dataset.idx,10);Jt(u)})})}document.querySelectorAll("#results-table th").forEach(e=>{e.classList.contains("no-sort")||e.addEventListener("click",()=>{const n=e.dataset.sort;_sortKey===n?_sortDir=_sortDir==="asc"?"desc":"asc":(_sortKey=n,_sortDir="asc"),nt()})});let $t=null;document.getElementById("search-input").addEventListener("input",e=>{const n=e.target.value;document.getElementById("search-clear").style.display=n?"":"none",clearTimeout($t),$t=setTimeout(()=>{_searchKeyword=n.trim(),nt(),Kt()},200)});document.getElementById("search-clear").addEventListener("click",()=>{const e=document.getElementById("search-input");e.value="",_searchKeyword="",document.getElementById("search-clear").style.display="none",nt(),Kt(),e.focus()});function Kt(){const e=document.getElementById("search-matches");if(!e)return;if(!_searchKeyword){e.textContent="";return}const n=_searchKeyword.toLowerCase();let a=0;for(const o of _results)[o.filename,o.merged_fields?.invoice_number,o.merged_fields?.seller_name,o.merged_fields?.buyer_name].filter(Boolean).join(" ").toLowerCase().includes(n)&&a++;e.textContent=t("search-matches",{n:a})}function Jt(e){_drawerIdx=e;const n=_results[e];if(!n)return;document.getElementById("drawer-title").textContent=n.filename;const a=n.engine==="cache"||n.from_cache,o=a?t("badge-cached-hint"):`${(n.elapsed_ms/1e3).toFixed(1)}s`;document.getElementById("drawer-sub").innerHTML=`
        <span>${n.page_count} ${t("pages-unit")} · ${escapeHtml(o)}</span>
        ${a?`<span class="engine-badge cached">${escapeHtml(t("badge-cached"))}</span>`:""}
        <span class="drawer-edit-count" id="drawer-edit-count-sub"></span>
    `,updateDrawerEditCount();const s=_userInfo&&_userInfo.can_edit_fields,i=_userInfo&&_userInfo.can_verify_tax,r=n.merged_fields,u=document.getElementById("drawer-body"),l=s?"":`
        <div class="drawer-readonly-banner">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="12" height="9" rx="1"/><path d="M7 9V6a3 3 0 016 0v3"/></svg>
            <span>${t("readonly-banner")}</span>
        </div>
    `,d=i?"":`<span class="tax-badge unverified" data-tip="${escapeHtml(t("tax-tip-unverified"))}">${t("tax-unverified")}</span>`;if(u.innerHTML=`
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
                ${be("wht_amount","drawer-lbl-wht-amount",r.wht_amount,"input",s,ra(r.wht_rate))}
            `:""}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 18V8h14v10M3 8l2-4h10l2 4M7 12h2M11 12h2"/></svg>
                ${t("drawer-sec-seller")}
            </div>
            ${be("seller_name","drawer-lbl-name",r.seller_name,"input",s)}
            ${be("seller_tax","drawer-lbl-tax",r.seller_tax,"input",s,d,Mt("seller"))}
            ${be("seller_addr","drawer-lbl-addr",r.seller_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="10" cy="6" r="3"/><path d="M3 18c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
                ${t("drawer-sec-buyer")}
            </div>
            ${be("buyer_name","drawer-lbl-name",r.buyer_name,"input",s)}
            ${be("buyer_tax","drawer-lbl-tax",r.buyer_tax,"input",s,d,Mt("buyer"))}
            ${be("buyer_addr","drawer-lbl-addr",r.buyer_addr,"textarea",s)}
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7l7-4 7 4v7l-7 4-7-4z"/><path d="M3 7l7 4 7-4M10 11v8"/></svg>
                ${t("drawer-sec-items")}
            </div>
            ${r.items&&r.items.length>0?la(r.items):`<div class="drawer-items-empty">${t("drawer-items-empty")}</div>`}
        </div>

        <div class="drawer-section">
            ${be("notes","drawer-lbl-notes",r.notes,"textarea",s)}
        </div>

        <details class="raw-text">
            <summary>${t("raw-text")}</summary>
            <pre>${escapeHtml(n.pages.map(c=>`--- Page ${c.page||c.page_number||"?"} ---
${c.raw_text||c.text||""}`).join(`

`))}</pre>
        </details>
    `,s?u.querySelectorAll("[data-field]").forEach(c=>{c.addEventListener("input",onFieldEdit)}):u.querySelectorAll("[data-field]").forEach(c=>{c.setAttribute("readonly","readonly")}),document.getElementById("drawer-mask").classList.add("show"),document.getElementById("drawer").classList.add("show"),injectOcrPushButton(),typeof window.bindDrawerClient=="function"){const c=n._historyId||n.history_id||null;window.bindDrawerClient(c,n.client_id||null)}typeof window.fillCategoryDatalist=="function"&&window.fillCategoryDatalist(),setTimeout(()=>{const c=document.getElementById("drawer-cat-input");c&&!c.value&&!c.readOnly&&c.focus()},80)}function ra(e){return e?`<span class="wht-badge">${escapeHtml(e)}%</span>`:""}function be(e,n,a,o,s,i,r){const u=_results[_drawerIdx],l=u&&u.edits[e]!==void 0?u.edits[e]:a,d=u&&u.edits[e]!==void 0&&u.edits[e]!==a,c=escapeHtml(l??""),p=s?"":"readonly",f=o==="textarea"?`<textarea data-field="${e}" rows="2">${c}</textarea>`:`<input type="text" data-field="${e}" value="${c}">`;return`
        <div class="drawer-field ${d?"edited":""} ${p}" data-field-wrap="${e}">
            <label class="drawer-field-label">
                <span class="drawer-field-edited-dot"></span>
                ${t(n)}
                ${i||""}
                ${r?`<span class="drawer-field-actions">${r}</span>`:""}
            </label>
            ${f}
        </div>
    `}function Mt(e){return _userInfo&&_userInfo.can_verify_tax?`
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
        </button>`}function la(e){return`
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
    `}function ca(){document.getElementById("drawer-mask").classList.remove("show"),document.getElementById("drawer").classList.remove("show");const e=document.getElementById("drawer-history-save");e&&e.remove();const n=document.getElementById("drawer-ocr-push");n&&n.remove();const a=document.getElementById("drawer-ocr-push-btn");a&&a.remove(),_drawerIdx=-1}window.renderResults=nt;window.openDrawer=Jt;window.closeDrawer=ca;function da(){const e=_results[_drawerIdx];if(!e||e._historyMode||!_userInfo||!_userInfo.can_push_erp||!e._historyId&&!e.history_id)return;const n=e._historyId||e.history_id,a=document.querySelector(".drawer-header");if(!a||document.getElementById("drawer-ocr-push-btn"))return;const o=(window._erpEndpoints||_erpEndpoints||[]).filter(function(u){return u&&u.enabled!==!1});if(o.length===0)return;const s=document.createElement("button");s.id="drawer-ocr-push-btn",s.className="drawer-push-btn";let i;if(o.length===1){const u=o[0].name||o[0].adapter||"ERP";i=t("btn-push-to-name",{name:u}),s.title=i}else i=t("btn-push-erp")+" ▾",s.title=t("btn-push-erp-pick-tip");s.innerHTML=`
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8h9M8 5l3 3-3 3"/>
            <rect x="11" y="3" width="3" height="10" rx="1"/>
        </svg>
        <span>${escapeHtml(i)}</span>
    `,s.addEventListener("click",function(u){u.preventDefault(),u.stopPropagation(),o.length===1?Yt(n,o[0].id):pa(s,n,o)});const r=a.querySelector(".drawer-diagnose");r?a.insertBefore(s,r):a.appendChild(s)}function pa(e,n,a){document.querySelectorAll(".drawer-push-picker").forEach(l=>l.remove());const o=e.getBoundingClientRect(),s=document.createElement("div");s.className="drawer-push-picker history-popover",s.style.position="fixed",s.style.top=o.bottom+6+"px",s.style.left=Math.max(8,o.right-240)+"px",s.style.minWidth="220px",s.style.zIndex="12000";const i=a.map(function(l){const d=escapeHtml(l.name||l.adapter||"ERP"),c=escapeHtml((l.adapter||"").toLowerCase()),f=l.is_default?'<span style="font-size:10px;color:#0a7a2c;background:#d6f5e0;padding:1px 6px;border-radius:999px;margin-left:6px;">'+escapeHtml(t("ep-default"))+"</span>":"";return'<button type="button" data-ep-id="'+escapeHtml(l.id)+'" style="display:flex;align-items:center;justify-content:space-between;width:100%;text-align:left;"><span><span style="color:#5d5d57;font-size:11px;margin-right:6px;">'+c+"</span>"+d+f+"</span></button>"}).join("");s.innerHTML=i,document.body.appendChild(s);const r=()=>{s.remove(),document.removeEventListener("click",u,!0)},u=l=>{!s.contains(l.target)&&l.target!==e&&!e.contains(l.target)&&r()};setTimeout(()=>document.addEventListener("click",u,!0),0),s.addEventListener("click",l=>{const d=l.target.closest("[data-ep-id]");if(!d)return;const c=d.getAttribute("data-ep-id");r(),Yt(n,c)})}async function Yt(e,n){const a=document.getElementById("drawer-ocr-push-btn");a&&(a.disabled=!0);try{const o={history_id:e};n&&(o.endpoint_id=n);const s=await fetch("/api/erp/push",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(o)}),i=await s.json();if(!s.ok){const r=i&&i.detail?i.detail:"err.unknown";r==="erp.no_default_endpoint"?showToast(t("erp-push-no-endpoint"),"warn"):r==="erp.endpoint_disabled"?(showToast(t("erp-push-disabled-tip")||t("card-disabled-tip")||"Endpoint disabled","warn"),typeof window._refreshErpEndpointsCache=="function"&&window._refreshErpEndpointsCache()):showToast(t("erp-push-fail",{err:r}),"fail");return}i.ok?showToast(t("erp-push-ok",{name:i.endpoint_name||""})):showToast(t("erp-push-fail",{err:i.error_msg||"unknown"}),"fail")}catch(o){showToast(t("erp-push-fail",{err:o.message}),"fail")}finally{a&&(a.disabled=!1)}}window.injectOcrPushButton=da;const ua=[{id:"input_vat",nameKey:"tpl-input-vat",descKey:"tpl-input-vat-desc",badge:"recommended"},{id:"standard",nameKey:"tpl-standard",descKey:"tpl-standard-desc"},{id:"sales_detail_th",nameKey:"export-tpl-sales-detail",descKey:"export-tpl-sales-detail-desc",badge:"new"},{id:"print",nameKey:"tpl-print",descKey:"tpl-print-desc"}];function Wt(){try{const e=localStorage.getItem("pn_export_tpl")||"input_vat";return e==="erp"?"input_vat":e}catch{return"input_vat"}}function fa(e){try{localStorage.setItem("pn_export_tpl",e||"input_vat")}catch{}}async function Xt(e){if(_results.length===0)return;e=e||"input_vat";const n=document.getElementById("btn-export");n&&(n.disabled=!0,n.classList.add("loading"));try{let a,o=`pearnly-export-${Date.now()}.xlsx`;if(e==="sales_detail_th"){const d=[];for(const c of _results){const p=c.invoices&&c.invoices.length>0?c.invoices:null;if(p&&p.length>1)for(let f=0;f<p.length;f++){const m=p[f]||{};d.push({filename:c.filename+" #"+(f+1)+"/"+p.length,engine:c.engine,merged_fields:m.fields||{}})}else d.push({filename:c.filename,engine:c.engine,merged_fields:c.merged_fields})}a=await apiPost("/api/ocr/export",{records:d,lang:currentLang,template:"sales_detail_th"})}else{const d=[];for(const p of _results)p.history_ids&&Array.isArray(p.history_ids)?d.push(...p.history_ids):p.history_id&&d.push(p.history_id);if(d.length===0){showToast(t("toast-export-error"),"error");return}const c=localStorage.getItem("mrpilot_token");a=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+c,"Content-Type":"application/json"},body:JSON.stringify({template:e,lang:currentLang,history_ids:d,client_id:null})}),o=`pearnly-${e}-${Date.now()}.xlsx`}if(!a)return;if(!a.ok){let d="HTTP "+a.status;try{const p=await a.json();p&&p.detail&&(d=typeof p.detail=="string"?p.detail:JSON.stringify(p.detail))}catch(p){console.warn("[export] resp.json err.detail parse failed:",p)}const c=typeof d=="string"&&d.indexOf(".")>0?"err."+d:null;showToast(c?t(c):t("toast-export-error")+" · "+d,"error");return}const s=await a.blob();let i=o;const r=a.headers.get("X-Filename");if(r)i=r;else{const c=(a.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(c)try{i=decodeURIComponent(c[1])}catch{}}const u=URL.createObjectURL(s),l=document.createElement("a");l.href=u,l.download=i,document.body.appendChild(l),l.click(),document.body.removeChild(l),URL.revokeObjectURL(u),showToast(t("toast-export-success"),"success")}catch(a){console.error(a),showToast(t("toast-export-error"),"error")}finally{n&&(n.disabled=!1,n.classList.remove("loading"))}}document.getElementById("btn-export").addEventListener("click",()=>{Xt(Wt())});function ma(){const e=document.getElementById("export-split-wrap");if(!e)return;let n=document.getElementById("export-dropdown");if(n){n.remove();return}n=document.createElement("div"),n.id="export-dropdown",n.className="export-dropdown";const a=Wt(),o=ua.map(i=>{const r=i.badge==="recommended"?`<span class="export-dd-badge badge-rec">${escapeHtml(t("report-recommended"))}</span>`:i.badge==="new"?`<span class="export-dd-badge badge-new">${escapeHtml(t("tpl-badge-new"))}</span>`:"";return`
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
    `;n.innerHTML=o+s,e.appendChild(n)}function dt(){const e=document.getElementById("export-dropdown");e&&e.remove()}const pt=document.getElementById("btn-export-arrow");pt&&pt.addEventListener("click",e=>{e.stopPropagation(),!pt.disabled&&ma()});document.addEventListener("click",e=>{const n=e.target.closest(".export-dd-item");if(n){const a=n.getAttribute("data-tpl");if(a==="__custom"){dt(),showToast(t("cs-coming-soon"),"info");return}fa(a),dt(),Xt(a);return}e.target.closest("#btn-export-arrow")||dt()});function va(){const e=document.getElementById("btn-export-arrow"),n=document.getElementById("btn-export");e&&n&&(e.disabled=n.disabled)}setInterval(va,300);function wt(){const e=document.getElementById("history-batch-bar"),n=document.getElementById("history-batch-count"),a=document.getElementById("history-check-all");if(!e||!n)return;const o=_historySelected.size;if(o>0?(e.style.display="",n.textContent=t("history-batch-count",{n:o})):e.style.display="none",a){const s=_historyState.items||[];if(s.length===0)a.checked=!1,a.indeterminate=!1;else{const i=s.filter(r=>_historySelected.has(r.id)).length;a.checked=i===s.length,a.indeterminate=i>0&&i<s.length}}}function ha(){_historySelected.clear(),wt()}async function _t(){if(!_userInfo){setTimeout(()=>_t(),300);return}const e=document.getElementById("history-free-block"),n=document.getElementById("history-main"),a=document.getElementById("history-empty");if(!e||!n||!a){console.warn("[History] container missing");return}if(!_userInfo.can_view_history){e.style.display="",n.style.display="none",a.style.display="none";return}e.style.display="none",_historyState.loading=!0;try{const o=_historyState.page*_historyState.pageSize,s=new URLSearchParams({limit:_historyState.pageSize,offset:o});_historyState.keyword&&s.set("keyword",_historyState.keyword);const i=typeof window.getCurrentClientId=="function"?window.getCurrentClientId():null;i&&s.set("client_id",String(i));const r=await fetch(`/api/history?${s}`,{headers:{Authorization:"Bearer "+token}});if(r.status===401){localStorage.removeItem("mrpilot_token");const d=await r.json().catch(()=>({}));if((typeof d.detail=="string"?d.detail:d.detail&&d.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}const u=await r.json();_historyState.items=u.items||[],_historyState.total=u.total||0;const l=new Set(_historyState.items.map(d=>d.id));for(const d of Array.from(_historySelected))l.has(d)||_historySelected.delete(d);Zt()}catch(o){console.error("load history failed",o)}finally{_historyState.loading=!1}}function Zt(){const e=document.getElementById("history-main"),n=document.getElementById("history-empty"),a=_historyState.items,o=document.getElementById("history-search-matches");if(o&&(o.textContent=_historyState.keyword?t("search-matches",{n:_historyState.total}):""),a.length===0&&_historyState.total===0&&!_historyState.keyword){e.style.display="none",n.style.display="";return}e.style.display="",n.style.display="none";let s=0;a.forEach(d=>{d.confidence==="high"&&s++});const i=a.length>0?Math.round(s/a.length*100):0;document.getElementById("history-stats").innerHTML=`
        <div class="rh-stat">
            <span class="rh-stat-label">${escapeHtml(t("history-total",{n:_historyState.total}))}</span>
        </div>
        <div class="rh-stat rh-stat-quality">
            <span class="rh-stat-dot"></span>
            <span class="rh-stat-label">${escapeHtml(t("history-avg-conf",{p:i}))}</span>
        </div>
    `;const r=document.getElementById("history-tbody");a.length===0?r.innerHTML=`<div class="history-row-empty">${escapeHtml(t("history-empty-title"))}</div>`:r.innerHTML=a.map(d=>{const c=new Date(d.created_at),p=String(c.getMonth()+1).padStart(2,"0"),f=String(c.getDate()).padStart(2,"0"),m=String(c.getHours()).padStart(2,"0"),b=String(c.getMinutes()).padStart(2,"0"),M=`${p}-${f} ${m}:${b}`,I=escapeHtml(d.filename||""),x=I.length>50?I.substring(0,50)+"…":I,y=d.invoice_no?escapeHtml(d.invoice_no):x,$=[];d.seller_name&&$.push(escapeHtml(d.seller_name)),d.invoice_no&&d.filename&&$.push(x);const C=$.join(" · ")||"-",F=d.category_tag?`<span class="history-badge category">${escapeHtml(d.category_tag)}</span>`:"",j=d.source_total&&d.source_total>1?`<span class="history-badge multi">${escapeHtml(t("invoice-part-of",{i:d.source_index||1,n:d.source_total}))}</span>`:"",_=d.total_amount!==null&&d.total_amount!==void 0?Number(d.total_amount).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):'<span class="history-cell-amount-empty">—</span>',h=[];(d.total_amount===null||d.total_amount===void 0)&&h.push(t("field-amount")),d.invoice_no||h.push(t("field-invoice-no")),d.invoice_date||h.push(t("field-invoice-date")),d.seller_name||h.push(t("field-seller-name")),h.length>0&&`${escapeHtml(d.id)}${escapeHtml(t("history-needs-review-tip")+" · "+h.join(" · "))}${escapeHtml(t("history-needs-review-tip"))}${svgIcon("alert",14)}`,d.edited&&`${escapeHtml(t("history-edited",{n:d.edit_count||1}))}`;const w=d.smart_assigned_flag?`<span class="history-badge smart-assigned" title="${escapeHtml(t("history-smart-assigned"))}">${svgIcon("sparkle",11)}</span>`:"",L=d.confidence==="high"?"high":d.confidence==="medium"?"mid":"low",S=d.confidence==="high"?t("conf-high"):d.confidence==="medium"?t("conf-medium"):t("conf-low"),D=`<span class="history-badge conf-${L}">${escapeHtml(S)}</span>`;let B="";const P=d.source||"manual";return P==="email"?B=`<span class="history-badge source source-email" title="${escapeHtml(t("history-source-email"))}">${svgIcon("mail",11)}<span>${escapeHtml(t("history-source-email"))}</span></span>`:P==="folder"?B=`<span class="history-badge source source-folder" title="${escapeHtml(t("history-source-folder"))}">${svgIcon("folder",11)}<span>${escapeHtml(t("history-source-folder"))}</span></span>`:P==="api"&&(B=`<span class="history-badge source source-api" title="${escapeHtml(t("history-source-api"))}">${svgIcon("api",11)}<span>${escapeHtml(t("history-source-api"))}</span></span>`),`
                <div class="history-row" data-hid="${escapeHtml(d.id)}">
                    <div class="history-cell-check">
                        <input type="checkbox" class="history-row-check" data-hid="${escapeHtml(d.id)}" ${_historySelected.has(d.id)?"checked":""} aria-label="select">
                    </div>
                    <div class="history-cell-date">${M}</div>
                    <div class="history-cell-file">
                        <div class="history-cell-filename">${y} ${F} ${j} ${B} ${w}</div>
                        <div class="history-cell-subtitle">${C}</div>
                    </div>
                    <div class="history-cell-amount">${_}</div>
                    <div class="history-cell-conf">${D}</div>
                    <div class="history-cell-menu">
                        <button class="history-menu-btn" data-hmenu="${escapeHtml(d.id)}" type="button" aria-label="menu">
                            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="3" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="13" cy="8" r="1.5"/></svg>
                        </button>
                    </div>
                </div>
            `}).join(""),wt();const u=a.length>0?_historyState.page*_historyState.pageSize+1:0,l=_historyState.page*_historyState.pageSize+a.length;document.getElementById("history-pager-info").textContent=t("history-pager",{from:u,to:l,total:_historyState.total}),document.getElementById("history-prev").disabled=_historyState.page===0,document.getElementById("history-next").disabled=(_historyState.page+1)*_historyState.pageSize>=_historyState.total}window.loadHistoryPage=_t;window.renderHistoryList=Zt;window.updateHistoryBatchBar=wt;window.clearHistorySelection=ha;typeof currentRoute<"u"&&currentRoute==="history"&&_t();async function Je(e){try{const n=await fetch(`/api/history/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=mergeFields(a.pages||[]),s={filename:a.filename,pages:a.pages,page_count:a.page_count,elapsed_ms:a.elapsed_ms,engine:"history",merged_fields:o,edits:{},confidence:a.confidence,archive_name:a.archive_name||null,category_tag:a.category_tag||null,_historyId:a.id,_historyMode:!0,client_id:a.client_id||null};_results.push(s),_drawerIdx=_results.length-1,openDrawer(_drawerIdx),ya(),typeof window.bindDrawerClient=="function"&&window.bindDrawerClient(a.id,a.client_id||null),ba(a.id)}catch(n){console.error("open history detail failed",n)}}async function ga(e){await Je(e),requestAnimationFrame(()=>{const n=document.querySelector('[data-field="total_amount"]');if(n){try{n.focus()}catch{}try{n.select()}catch{}try{n.scrollIntoView({block:"center",behavior:"smooth"})}catch{}}})}function ya(){const e=document.getElementById("drawer-body");if(!e||document.getElementById("drawer-history-save"))return;const n=document.createElement("div");n.id="drawer-history-save",n.className="drawer-history-save-bar",n.innerHTML=`
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
    `,e.appendChild(n),document.getElementById("btn-save-history").addEventListener("click",_a),document.getElementById("btn-push-erp").addEventListener("click",wa)}async function ba(e){}async function wa(){showToast(t("erp-push-coming-soon")||"ERP 推送即将开放，敬请期待","info")}async function _a(){const e=_results[_drawerIdx];if(!e||!e._historyId)return;const n=JSON.parse(JSON.stringify(e.pages||[]));if(n.length>0){const o=n.findIndex(u=>!u.is_duplicate&&!u.is_copy),s=o>=0?o:0,i=n[s].fields||(n[s].fields={}),r={...e.edits};r.category_tag!==void 0&&(r.category=r.category_tag,delete r.category_tag),Object.assign(i,r)}const a=document.getElementById("btn-save-history");a&&(a.disabled=!0);try{if(!(await fetch(`/api/history/${encodeURIComponent(e._historyId)}`,{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({pages:n})})).ok)throw new Error("save failed");showAlert("info",t("history-save-ok")),setTimeout(hideAlerts,1500),closeDrawer(),e._historyMode&&_results.pop(),loadHistoryPage()}catch{showAlert("error",t("history-save-fail")),a&&(a.disabled=!1)}}function ka(e,n){document.querySelectorAll(".history-popover").forEach(d=>d.remove());const a=n.getBoundingClientRect(),o=(_historyState.items||[]).find(d=>d.id===e),s=o&&o.invoice_no?String(o.invoice_no):"",i=o&&o.has_pdf===!0,r=document.createElement("div");r.className="history-popover",r.innerHTML=`
        <button data-act="copy-invno" ${s?"":"disabled"}>${escapeHtml(t("history-menu-copy-invno"))}</button>
        <button data-act="download-pdf" ${i?"":"disabled"}>${escapeHtml(t("history-menu-download-pdf"))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t("history-menu-delete"))}</button>
    `,r.style.top=a.bottom+4+"px",r.style.left=a.right-160+"px",document.body.appendChild(r);const u=()=>{r.remove(),document.removeEventListener("click",l,!0)},l=d=>{!r.contains(d.target)&&d.target!==n&&u()};setTimeout(()=>document.addEventListener("click",l,!0),0),r.addEventListener("click",async d=>{const c=d.target.closest("[data-act]");if(!c||c.disabled)return;const p=c.dataset.act;if(u(),p==="copy-invno"){if(!s)return;try{await navigator.clipboard.writeText(s),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{try{const m=document.createElement("textarea");m.value=s,m.style.position="fixed",m.style.opacity="0",document.body.appendChild(m),m.select(),document.execCommand("copy"),document.body.removeChild(m),showToast(t("history-copy-invno-ok",{no:s}),"success")}catch{showToast(t("history-copy-invno-fail"),"error")}}}else if(p==="download-pdf"){const f=showToast(t("history-download-pdf-loading"),"loading",0);try{const m=await fetch(`/api/history/${encodeURIComponent(e)}/pdf`,{headers:{Authorization:"Bearer "+token}});if(!m.ok)throw new Error("download failed");const b=await m.blob(),M=URL.createObjectURL(b),I=document.createElement("a");I.href=M,I.download=o&&o.filename?o.filename.endsWith(".pdf")?o.filename:o.filename+".pdf":"invoice.pdf",document.body.appendChild(I),I.click(),document.body.removeChild(I),setTimeout(()=>URL.revokeObjectURL(M),5e3),f(),showToast(t("history-download-pdf-ok"),"success")}catch{f(),showToast(t("history-download-pdf-fail"),"error")}}else if(p==="delete"){if(!await showConfirm(t("history-confirm-delete"),{danger:!0}))return;try{if(!(await fetch(`/api/history/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showAlert("info",t("history-delete-ok")),setTimeout(hideAlerts,1500),loadHistoryPage()}catch{showAlert("error",t("history-delete-fail"))}}})}(function(){document.addEventListener("click",r=>{const u=r.target.closest(".history-row"),l=r.target.closest("[data-hmenu]");if(l){r.stopPropagation(),ka(l.dataset.hmenu,l);return}const d=r.target.closest("[data-review]");if(d){r.stopPropagation(),Je(d.dataset.review);return}const c=r.target.closest("[data-fill-amount]");if(c){r.stopPropagation(),ga(c.dataset.fillAmount);return}r.target.closest(".history-row-check")||r.target.closest(".history-cell-check")||u&&!r.target.closest("[data-hmenu]")&&Je(u.dataset.hid)});const n=document.getElementById("history-tbody");n&&n.addEventListener("change",r=>{const u=r.target.closest(".history-row-check");if(!u)return;const l=u.dataset.hid;u.checked?_historySelected.add(l):_historySelected.delete(l),updateHistoryBatchBar()});const a=document.getElementById("history-check-all");a&&a.addEventListener("change",r=>{const u=r.target.checked;for(const l of _historyState.items)u?_historySelected.add(l.id):_historySelected.delete(l.id);document.querySelectorAll(".history-row-check").forEach(l=>{l.checked=u}),updateHistoryBatchBar()});const o=document.getElementById("history-batch-cancel");o&&o.addEventListener("click",()=>{clearHistorySelection(),document.querySelectorAll(".history-row-check").forEach(r=>{r.checked=!1})});const s=document.getElementById("history-batch-delete");s&&s.addEventListener("click",async()=>{const r=_historySelected.size;if(r===0||!await showConfirm(t("history-batch-confirm",{n:r}),{danger:!0}))return;const l=Array.from(_historySelected);try{const d=await fetch("/api/history/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({ids:l})});if(!d.ok)throw new Error("batch delete failed");const c=await d.json();showToast(t("history-batch-done",{n:c.deleted||0}),"success"),clearHistorySelection(),loadHistoryPage()}catch(d){console.error("batch delete",d),showToast(t("history-batch-fail"),"error")}});let i=null;document.getElementById("history-search").addEventListener("input",r=>{const u=r.target.value;document.getElementById("history-search-clear").style.display=u?"":"none",clearTimeout(i),i=setTimeout(()=>{_historyState.keyword=u.trim(),_historyState.page=0,clearHistorySelection(),loadHistoryPage()},300)}),document.getElementById("history-search-clear").addEventListener("click",()=>{const r=document.getElementById("history-search");r.value="",_historyState.keyword="",_historyState.page=0,clearHistorySelection(),document.getElementById("history-search-clear").style.display="none",loadHistoryPage(),r.focus()}),document.getElementById("history-range").addEventListener("change",r=>{_historyState.range=parseInt(r.target.value,10),_historyState.page=0,clearHistorySelection(),loadHistoryPage()}),document.getElementById("history-prev").addEventListener("click",()=>{_historyState.page>0&&(_historyState.page--,clearHistorySelection(),loadHistoryPage())}),document.getElementById("history-next").addEventListener("click",()=>{(_historyState.page+1)*_historyState.pageSize<_historyState.total&&(_historyState.page++,clearHistorySelection(),loadHistoryPage())})})();window.openHistoryDrawer=Je;const Me=document.getElementById("drop-zone"),kt=document.getElementById("file-input");Me.addEventListener("click",()=>kt.click());kt.addEventListener("change",e=>Qt(e.target.files));["dragover","dragenter"].forEach(e=>{Me.addEventListener(e,n=>{n.preventDefault(),Me.classList.add("drag-over")})});["dragleave","drop"].forEach(e=>{Me.addEventListener(e,n=>{n.preventDefault(),Me.classList.remove("drag-over")})});Me.addEventListener("drop",e=>{e.preventDefault(),Qt(e.dataTransfer.files)});const xa=/\.(pdf|png|jpe?g|webp|tiff?|bmp|gif|xlsx?|xlsm|csv|tsv|docx?|txt)$/i;function mt(e){return e.type&&e.type.startsWith("image/")||/\.(png|jpe?g|webp|tiff?|bmp|gif)$/i.test(e.name)}function Ea(e){return e.type==="application/pdf"||/\.pdf$/i.test(e.name)}function Ia(e){return Ea(e)||mt(e)||xa.test(e.name)}function Qt(e){hideAlerts();const n=Array.from(e),a=n.filter(Ia);a.length!==n.length&&showAlert("warn",t("alert-unsupported-format"));const o=a.filter(u=>!mt(u)),s=a.filter(mt),i=new Set(_selectedFiles.map(u=>u.name+"_"+u.size));for(const u of o){const l=u.name+"_"+u.size;i.has(l)||(_selectedFiles.push({file:u,name:u.name,size:u.size,status:"waiting",errorKey:null,errorParams:null}),i.add(l))}if(s.length>0)try{handleCameraImages(s,"gallery")}catch(u){console.error("[upload] image route failed",u)}const r=getMaxFiles();_selectedFiles.length>r&&(showAlert("warn",t("alert-file-count",{n:r})),_selectedFiles=_selectedFiles.slice(0,r)),at(),xt(),kt.value=""}let Ve=!1;function at(){const e=document.getElementById("file-list");if(!e)return;if(_selectedFiles.length===0){e.classList.remove("has-files"),e.innerHTML="";return}e.classList.add("has-files");const n=_selectedFiles.length,a=_selectedFiles.filter(p=>p.status==="processing"||p.status==="retrying").length,o=_selectedFiles.filter(p=>p.status==="success").length,s=_selectedFiles.filter(p=>p.status==="error").length;let i=`<span class="count">${escapeHtml(t("file-list-total",{n}))}</span>`;const r=[];a&&r.push(`<span style="color: var(--accent, #111111);">${a} ${escapeHtml(t("status-processing"))}</span>`),o&&r.push(`<span style="color: var(--success, #059669);">${o} ${escapeHtml(t("status-success"))}</span>`),s&&r.push(`<span style="color: var(--danger, #dc2626);">${s} ${escapeHtml(t("status-error"))}</span>`),r.length&&(i+=" · "+r.join(" · "));const u=Ve?t("file-list-collapse"):t("file-list-expand"),l=_selectedFiles.map((p,f)=>{let m=t("status-"+p.status);p.status==="retrying"&&(m=t("status-retrying")),p.status==="error"&&p.errorKey&&(m=t(p.errorKey,p.errorParams||{}));const b=p.status==="processing"||p.status==="retrying"?'<span class="spinner"></span>':"",M=p.status==="error"&&p.canRetry?`<button class="file-retry-btn" data-retry-idx="${f}" title="${escapeHtml(t("upload-retry-btn"))}">${svgIcon("refresh",12)}<span>${escapeHtml(t("upload-retry-btn"))}</span></button>`:"",I=p.status==="success"&&p.fromCache?`<span class="file-cache-badge">${svgIcon("cache",11)}<span>${escapeHtml(t("cache-hit-badge"))}</span></span>`:"";return`
            <li class="file-item">
                <svg class="file-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 2h7l4 4v12H5z"/><path d="M12 2v4h4"/></svg>
                <span class="file-name" title="${escapeHtml(p.name)}">${escapeHtml(p.name)}</span>
                ${I}
                <span class="file-status ${p.status}">${b}${m}</span>
                ${M}
            </li>
        `}).join("");e.innerHTML=`
        <div class="file-list-head">
            <div>${i}</div>
            ${n>5?`<button class="toggle" id="file-list-toggle">${escapeHtml(u)}</button>`:""}
        </div>
        <ul class="file-list-body${Ve?" expanded":""}" id="file-list-body">
            ${l}
        </ul>
    `;const d=document.getElementById("file-list-toggle");d&&d.addEventListener("click",()=>{Ve=!Ve,at()});const c=document.getElementById("file-list-body");c&&!c.dataset.retryBound&&(c.dataset.retryBound="1",c.addEventListener("click",async p=>{const f=p.target.closest(".file-retry-btn");if(!f)return;const m=parseInt(f.dataset.retryIdx||"-1",10);if(m<0||m>=_selectedFiles.length)return;const b=_selectedFiles[m];!b||b.status!=="error"||typeof window._reprocessFile=="function"&&await window._reprocessFile(b,!0)}))}function xt(){const e=document.getElementById("btn-start"),n=document.getElementById("btn-clear"),a=document.getElementById("btn-export"),o=_selectedFiles.some(s=>s.status==="waiting");e.disabled=_selectedFiles.length===0||!o,n.disabled=_selectedFiles.length===0&&_results.length===0,a.disabled=_results.length===0}document.getElementById("btn-clear").addEventListener("click",()=>{_selectedFiles=[],_results=[],at(),renderResults(),xt(),hideAlerts()});window.renderFileList=at;window.updateStartButton=xt;(function(){const n=document.getElementById("upload-alt-row"),a=document.getElementById("gallery-input"),o=document.getElementById("camera-input");if(!n)return;n.style.display="";const s=document.getElementById("btn-scan-doc");s&&o&&(s.addEventListener("click",async()=>{!(localStorage.getItem("mrpilot_camera_tips_skip")==="1")&&!await La()||o.click()}),o.addEventListener("change",async u=>{const l=Array.from(u.target.files||[]);if(u.target.value="",l.length!==0)for(const d of l)await vt([d],"camera")}));const i=document.getElementById("btn-upload-pic");i&&a&&i.addEventListener("click",()=>a.click());const r=u=>async l=>{const d=Array.from(l.target.files||[]);if(l.target.value="",d.length===0)return;const c=d.filter(f=>f.type==="application/pdf"||/\.pdf$/i.test(f.name)),p=d.filter(f=>!c.includes(f));c.length>0&&await Ba(c),p.length>0&&await vt(p,u)};a&&a.addEventListener("change",r("gallery"))})();async function Ba(e){for(const a of e)_selectedFiles.push({file:a,name:a.name,size:a.size,status:"waiting",errorKey:null,errorParams:null});const n=getMaxFiles();_selectedFiles.length>n&&(showAlert("warn",t("alert-file-count",{n})),_selectedFiles=_selectedFiles.slice(0,n)),renderFileList(),updateStartButton()}function La(){return new Promise(e=>{const n=document.getElementById("camera-tips-modal"),a=document.getElementById("camera-tips-ok"),o=document.getElementById("camera-tips-cancel"),s=document.getElementById("camera-tips-skip");if(!n||!a){e(!0);return}s&&(s.checked=!1),n.style.display="flex";const i=u=>{n.style.display="none",s&&s.checked&&localStorage.setItem("mrpilot_camera_tips_skip","1"),a.onclick=null,o&&(o.onclick=null),n.onclick=null,document.removeEventListener("keydown",r),e(u)},r=u=>{u.key==="Escape"&&i(!1)};a.onclick=()=>i(!0),o&&(o.onclick=()=>i(!1)),n.onclick=u=>{u.target===n&&i(!1)},document.addEventListener("keydown",r),setTimeout(()=>a.focus(),50)})}async function Ye(e){return new Promise(n=>{const a=new FileReader;a.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),a.onload=()=>{const o=new Image;o.onerror=()=>n({warnings:[],width:0,height:0,brightness:128}),o.onload=()=>{const s=[],i=o.naturalWidth,r=o.naturalHeight;(i<1e3||r<1e3)&&s.push("low_res");try{const u=document.createElement("canvas");u.width=64,u.height=64;const l=u.getContext("2d");l.drawImage(o,0,0,64,64);const d=l.getImageData(0,0,64,64).data;let c=0,p=0;for(let m=0;m<d.length;m+=4)c+=.299*d[m]+.587*d[m+1]+.114*d[m+2],p++;const f=p?c/p:128;f<70?s.push("too_dark"):f>235&&s.push("too_bright"),n({warnings:s,width:i,height:r,brightness:f})}catch{n({warnings:s,width:i,height:r,brightness:128})}},o.src=a.result},a.readAsDataURL(e)})}let _e=[],Le=null;async function vt(e,n){if(hideAlerts(),!(!e||e.length===0)){if(typeof window.jspdf>"u"||!window.jspdf.jsPDF){showToast(t("camera-loading"),"info");for(let a=0;a<30&&(await new Promise(o=>setTimeout(o,100)),!(window.jspdf&&window.jspdf.jsPDF));a++);if(!window.jspdf||!window.jspdf.jsPDF){showToast(t("camera-lib-fail"),"error");return}}if(n==="camera"&&e.length===1){const a=e[0];let o={};try{o=await Ye(a)}catch{}_e.push({file:a,quality:o}),Le="camera",$e();return}if(n==="gallery"&&(e.length>=2||_e.length>0)){for(const a of e){let o={};try{o=await Ye(a)}catch{}_e.push({file:a,quality:o})}Le="gallery",$e();return}await en(e)}}async function Sa(e){const n=new Set;for(const o of e)try{((await Ye(o)).warnings||[]).forEach(i=>n.add(i))}catch{}try{const o=await tn(e);o&&_selectedFiles.push({file:o,name:o.name,size:o.size,status:"waiting",errorKey:null,errorParams:null})}catch(o){console.error("[camera] convert failed",o),showToast(t("camera-convert-fail"),"error");return}const a=getMaxFiles();_selectedFiles.length>a&&(showAlert("warn",t("alert-file-count",{n:a})),_selectedFiles=_selectedFiles.slice(0,a)),renderFileList(),updateStartButton(),showToast(t("camera-added-merged",{n:e.length}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}function $e(){let e=document.getElementById("camera-buffer-bar");if(_e.length===0){e&&e.remove(),Le=null;return}e||(e=document.createElement("div"),e.id="camera-buffer-bar",e.className="camera-buffer-bar",document.body.appendChild(e));const n=_e.length,a=n>=2,o=Le==="gallery",s=o?t("camera-buffer-more-gallery"):t("camera-buffer-more");let i;a?o?i=`
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
    `,e.querySelector('[data-cbb-action="discard"]').onclick=()=>{_e=[],Le=null,$e()},e.querySelector('[data-cbb-action="more"]').onclick=()=>{const l=o?"gallery-input":"camera-input",d=document.getElementById(l);d&&d.click()};const r=e.querySelector('[data-cbb-action="merge"]');r&&(r.onclick=async()=>{const l=_e.map(d=>d.file);_e=[],Le=null,$e(),await Sa(l)});const u=e.querySelector('[data-cbb-action="separate"]');u&&(u.onclick=async()=>{const l=_e.map(d=>d.file);_e=[],Le=null,$e(),await en(l)})}typeof window.subscribeI18n=="function"&&window.subscribeI18n("camera-buffer-bar",()=>{_e.length>0&&$e()});async function en(e){const n=new Set;let a=0;for(const s of e)try{((await Ye(s)).warnings||[]).forEach(u=>n.add(u));const r=await tn([s]);r&&(_selectedFiles.push({file:r,name:r.name,size:r.size,status:"waiting",errorKey:null,errorParams:null}),a++)}catch(i){console.error("[camera] separate convert failed",i)}if(a===0){showToast(t("camera-convert-fail"),"error");return}const o=getMaxFiles();_selectedFiles.length>o&&(showAlert("warn",t("alert-file-count",{n:o})),_selectedFiles=_selectedFiles.slice(0,o)),renderFileList(),updateStartButton(),showToast(t("camera-added-separate",{n:a}),"success"),n.size>0&&setTimeout(()=>{n.has("too_dark")?showToast(t("camera-quality-dark"),"warn"):n.has("low_res")?showToast(t("camera-quality-lowres"),"warn"):n.has("too_bright")&&showToast(t("camera-quality-overexposed"),"warn")},1e3)}async function tn(e){if(!e||e.length===0)return null;const{jsPDF:n}=window.jspdf,a=210,o=297,s=new n({unit:"mm",format:"a4",orientation:"p"});for(let d=0;d<e.length;d++){const c=e[d],{dataUrl:p,naturalW:f,naturalH:m}=await Ca(c);d>0&&s.addPage("a4","p");const b=f/m;let M=a-10,I=M/b;I>o-10&&(I=o-10,M=I*b);const x=(a-M)/2,y=(o-I)/2,$=c.type==="image/png"?"PNG":"JPEG";s.addImage(p,$,x,y,M,I,void 0,"FAST")}const i=s.output("blob"),r=new Date,u=r.getFullYear().toString()+String(r.getMonth()+1).padStart(2,"0")+String(r.getDate()).padStart(2,"0")+String(r.getHours()).padStart(2,"0")+String(r.getMinutes()).padStart(2,"0")+String(r.getSeconds()).padStart(2,"0"),l=e.length>1?`_${e.length}p`:"";return new File([i],`photo_${u}${l}.pdf`,{type:"application/pdf"})}function Ca(e){return new Promise((n,a)=>{const o=new FileReader;o.onerror=a,o.onload=()=>{const s=new Image;s.onerror=a,s.onload=()=>n({dataUrl:o.result,naturalW:s.naturalWidth,naturalH:s.naturalHeight}),s.src=o.result},o.readAsDataURL(e)})}window.handleCameraImages=vt;document.getElementById("btn-start").addEventListener("click",async()=>{if(hideAlerts(),document.getElementById("btn-start").disabled=!0,_userInfo&&_userInfo.plan==="free"){const c=await fetch("/api/health").then(p=>p.json()).catch(()=>null);c&&!c.ocr_ready&&(showAlert("info",t("alert-loading-engine")),startEnginePolling())}const e=_selectedFiles.filter(c=>c.status==="waiting"),n=6;async function a(c,p){if(window._ocrAborted)return c.status="cancelled",c.errorKey=null,renderFileList(),{};c.status=p?"retrying":"processing",c.canRetry=!1,renderFileList();const f=new AbortController,m=setTimeout(()=>f.abort("timeout"),9e4);window._ocrCtrls=window._ocrCtrls||new Set,window._ocrCtrls.add(f);try{const b=new FormData;b.append("file",c.file,c.name);try{if(typeof window.getCurrentClientId=="function"){const $=window.getCurrentClientId();$!=null&&b.append("client_id",String($))}}catch{}const M=await fetch("/api/ocr/recognize",{method:"POST",headers:{Authorization:"Bearer "+token},body:b,signal:f.signal});if(clearTimeout(m),window._ocrCtrls.delete(f),M.status===401||M.status===403){const C=await M.clone().json().catch(()=>({})),F=C&&C.detail,j=typeof F=="string"?F:F&&F.code||"";if(!j||j.startsWith("auth.")){if(localStorage.removeItem("mrpilot_token"),j==="auth.session_revoked")_showSessionRevokedModal();else{const _=j==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";showToast(t(_),"error"),setTimeout(()=>{window.location.href="/"},1200)}return{abort:!0}}j==="quota.need_api_key"&&showToast(t("err.quota.need_api_key"),"error")}if(!M.ok){const C=(await M.json().catch(()=>({}))).detail;return typeof C=="string"?(c.errorKey="err."+C,c.errorParams=null):C&&C.code?(c.errorKey="err."+C.code,c.errorParams={...C,mb:_quota.max_file_size_mb}):(c.errorKey="err.unknown",c.errorParams=null),(c.errorKey==="err.unknown"||c.errorKey==="err.ocr.engine_error")&&(M.status===429?c.errorKey="err.rate_limit":M.status===502||M.status===503||M.status===504?c.errorKey="err.gemini_overloaded":M.status>=500&&(c.errorKey="err.server")),c.status="error",c.canRetry=!/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(c.errorKey||""),renderFileList(),{}}const I=await M.json();c.status="success",c.fromCache=!!I.from_cache;const x=mergeFields(I.pages),y=I.confidence||(x.items&&x.items.length>0?"high":"low");if(_results.push({filename:I.filename,pages:I.pages,page_count:I.page_count,elapsed_ms:I.elapsed_ms,engine:I.engine,merged_fields:x,edits:{},confidence:y,history_id:I.history_id,history_ids:I.history_ids||[],invoice_count:I.invoice_count||1,invoices:I.invoices||[],archive_name:I.archive_name||null,category_tag:I.category_tag||null,auto_pushed:!!I.auto_pushed,typhoon_enhanced:!!I.typhoon_enhanced,typhoon_pages:I.typhoon_pages||[],from_cache:!!I.from_cache}),I.invoice_count&&I.invoice_count>1&&showToast(t("multi-invoice-toast",{file:I.filename,n:I.invoice_count}),"success"),I.missed_invoice_warnings&&I.missed_invoice_warnings.length){const $=I.missed_invoice_warnings.map(function(C){return C.page}).filter(function(C){return C!=null});showToast(t("missed-invoice-warn",{file:I.filename,pages:$.join(", ")}),"warn",8e3),console.warn("[OCR] possible missed invoice(s)",I.missed_invoice_warnings)}if(I.typhoon_enhanced&&I.typhoon_pages&&I.typhoon_pages.length&&showToast(t("typhoon-enhanced-toast",{file:I.filename,n:I.typhoon_pages.length}),"success"),I.fallback_used){const $=I.engine_chain||[],C=I.engine||"";let F;C==="typhoon_nvidia"?F="fallback-typhoon-nvidia-toast":C==="easyocr"?F="fallback-easyocr-toast":F="fallback-generic-toast",showToast(t(F,{file:I.filename}),"warn"),console.info("[OCR Chain]",$)}if(I.from_cache&&showToast(t("cache-hit-toast",{file:I.filename}),"info"),I.duplicate_warnings&&I.duplicate_warnings.length){window._dupQueue||(window._dupQueue=[]);for(const $ of I.duplicate_warnings)window._dupQueue.push({filename:I.filename,...$})}return I.auto_pushed&&showToast(t("auto-push-fired",{file:I.filename}),"info"),I.quota&&I.quota.used_this_month!=null&&_userInfo&&(_userInfo.used_this_month=I.quota.used_this_month,_userInfo.tenant_used=I.quota.used_this_month,renderInfoBar(),renderQuotaBanner()),renderFileList(),renderResults(),updateStartButton(),{}}catch(b){clearTimeout(m);try{window._ocrCtrls&&window._ocrCtrls.delete(f)}catch{}console.error("[Upload] failed for",c.file.name,b);const M=b&&(b.name==="AbortError"||b==="timeout"),I=M&&(f.signal.reason==="timeout"||b==="timeout"),x=b&&b.message&&/NetworkError|Failed to fetch/i.test(b.message);return M&&(f.signal.reason==="user_stop"||window._ocrAborted)?(c.status="cancelled",c.errorKey=null,c.canRetry=!1,renderFileList(),{}):(I?c.errorKey="err.timeout":M?c.errorKey="err.aborted":x?c.errorKey="err.network":(c.errorKey="err.unknown",c.errorParams={msg:b&&b.message?b.message:String(b)}),c.status="error",!p&&!window._ocrAborted&&(x||I)&&navigator.onLine!==!1&&(c.canRetry=!0,renderFileList(),await new Promise($=>setTimeout($,2e3)),c.status==="error"&&navigator.onLine!==!1&&!window._ocrAborted)?a(c,!0):(c.canRetry=!0,renderFileList(),{}))}}window._reprocessFile=a;let o=0,s=!1;async function i(){for(;o<e.length&&!s&&!window._ocrAborted;){const c=o++,p=await a(e[c]);if(p&&p.abort){s=!0;return}}}window._ocrAborted=!1,window._ocrCtrls=window._ocrCtrls||new Set;const r=document.getElementById("btn-start"),u=document.getElementById("btn-stop");r&&(r.style.display="none"),u&&(u.style.display="");try{typeof window._bigBatchStart=="function"&&window._bigBatchStart(e)}catch{}const l=[];for(let c=0;c<Math.min(n,e.length);c++)l.push(i());await Promise.all(l);try{typeof window._bigBatchStop=="function"&&window._bigBatchStop()}catch{}r&&(r.style.display=""),u&&(u.style.display="none");const d=!!window._ocrAborted;window._ocrAborted=!1,window._ocrCtrls.clear(),updateStartButton(),stopEnginePolling(),document.getElementById("alert-info").classList.contains("show")&&(showAlert("info",t("alert-engine-ready")),setTimeout(hideAlerts,2e3));try{const c={success:0,cancelled:0,network:0,timeout:0,quota:0,overloaded:0,rate:0,other:0};for(const f of e)if(f.status==="success")c.success++;else if(f.status==="cancelled")c.cancelled++;else if(f.status==="error"){const m=f.errorKey||"";m==="err.network"?c.network++:m==="err.timeout"||m==="err.aborted"?c.timeout++:m.indexOf("quota")>=0||m==="err.monthly_limit_exceeded"?c.quota++:m==="err.gemini_overloaded"||m==="err.server"?c.overloaded++:m==="err.rate_limit"?c.rate++:c.other++}const p=e.length;d?showToast(Ta(c,p),"warn",4e3):p>1&&c.network+c.timeout+c.quota+c.overloaded+c.rate+c.other>0&&showToast($a(c),"error",4500)}catch{}window._dupQueue&&window._dupQueue.length&&showDuplicateDialog()});function Ta(e,n){return t("ocr-summary-aborted").replace("{success}",e.success).replace("{cancelled}",e.cancelled).replace("{total}",n)}function $a(e){const n=[];return e.success&&n.push(t("ocr-summary-success").replace("{n}",e.success)),e.network&&n.push(t("ocr-summary-network").replace("{n}",e.network)),e.timeout&&n.push(t("ocr-summary-timeout").replace("{n}",e.timeout)),e.quota&&n.push(t("ocr-summary-quota").replace("{n}",e.quota)),e.overloaded&&n.push(t("ocr-summary-overloaded").replace("{n}",e.overloaded)),e.rate&&n.push(t("ocr-summary-rate").replace("{n}",e.rate)),e.other&&n.push(t("ocr-summary-other").replace("{n}",e.other)),n.join(" · ")}document.addEventListener("click",e=>{if(!e.target.closest("#btn-stop")||window._ocrAborted)return;window._ocrAborted=!0,window._ocrCtrls&&window._ocrCtrls.size&&window._ocrCtrls.forEach(a=>{try{a.abort("user_stop")}catch{}});const n=document.getElementById("btn-stop");n&&(n.disabled=!0),typeof showToast=="function"&&showToast(t("ocr-stop-toast"),"warn",2e3),setTimeout(()=>{n&&(n.disabled=!1)},800)});function nn(){if(!window._dupQueue||!window._dupQueue.length)return;const e=window._dupQueue.shift(),n=e.level==="exact",a=n?"dup-title-exact":"dup-title-likely",o=n?"dup-desc-exact":"dup-desc-likely",s=n?"#DC2626":"#D97706",i=n?"#FEE2E2":"#FEF3C7",r=m=>m!=null?Number(m).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—",u=m=>m||"—",l=m=>{try{const b=new Date(m);return`${b.getFullYear()}-${String(b.getMonth()+1).padStart(2,"0")}-${String(b.getDate()).padStart(2,"0")}`}catch{return m}},d=e.invoice_total>1?` · ${t("invoice-part-of",{i:e.invoice_index,n:e.invoice_total})}`:"",c=(e.matched_fields||[]).map(m=>{const b=t("dup-field-"+m.replace("_","-"))||m;return`<span class="dup-field-chip">${escapeHtml(b)}</span>`}).join(" "),p=document.createElement("div");p.className="log-detail-modal",p.innerHTML=`
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
                <div class="dup-matched-label">${escapeHtml(t("dup-matched-on"))} ${c}</div>
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
                        <tr><td>${escapeHtml(t("dup-field-invoice-date"))}</td><td>${escapeHtml(u(e.current.invoice_date))}</td><td>${escapeHtml(u(e.match.invoice_date))}</td></tr>
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
    `,document.body.appendChild(p);const f=()=>{p.remove(),window._dupQueue&&window._dupQueue.length&&setTimeout(nn,200)};p.querySelector(".dup-close").addEventListener("click",f),p.querySelector('[data-action="view"]').addEventListener("click",()=>{const m=e.match.id;window.location.hash="#/history",setTimeout(()=>{typeof openHistoryDrawer=="function"&&openHistoryDrawer(m)},400),f()}),p.querySelector('[data-action="delete"]').addEventListener("click",async()=>{const m=e.new_history_id;if(!m){f();return}try{(await fetch(`/api/history/${encodeURIComponent(m)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok?showToast(t("dup-deleted-toast"),"success"):showToast(t("dup-delete-failed"),"error")}catch{showToast(t("dup-delete-failed"),"error")}f()}),p.querySelector('[data-action="keep"]').addEventListener("click",f)}window.showDuplicateDialog=nn;function Ce(e,n){try{return typeof window.t=="function"?window.t(e):n}catch{return n}}function je(e){if(e==null||isNaN(e))return"—";try{return String(e).replace(/\B(?=(\d{3})+(?!\d))/g,",")}catch{return String(e)}}function Ma(e){if(!e)return"";try{const n=new Date(e).getTime();if(!n)return"";const a=Math.floor((Date.now()-n)/1e3);return a<60?Ce("time-just-now","刚刚"):a<3600?Math.floor(a/60)+Ce("time-min-ago-suffix"," 分钟前"):a<86400?Math.floor(a/3600)+Ce("time-hour-ago-suffix"," 小时前"):Math.floor(a/86400)+Ce("time-day-ago-suffix"," 天前")}catch{return""}}async function Et(){an();const e=document.getElementById("dash-kpi-invoices"),n=document.getElementById("dash-kpi-pending"),a=document.getElementById("dash-kpi-exceptions"),o=document.getElementById("dash-kpi-plan"),s=document.getElementById("dash-kpi-plan-sub"),i=document.getElementById("dash-recent-list"),r=document.getElementById("dash-quick-exc-badge");try{const u={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},[l,d,c]=await Promise.all([fetch("/api/me/tenant-usage",{headers:u}).then(I=>I.ok?I.json():null).catch(()=>null),fetch("/api/history?limit=20",{headers:u}).then(I=>I.ok?I.json():null).catch(()=>null),fetch("/api/exceptions/stats?status=pending",{headers:u}).then(I=>I.ok?I.json():null).catch(()=>null)]),p=l&&l.ocr_this_month||0;let f=0;const m=d&&(d.items||d.history||d)||[],b=Array.isArray(m)?m:[];b.forEach(I=>{(I.status==="pending"||I.status==="reviewing")&&f++});const M=c&&(c.total||c.count||c.pending||0)||0;if(e&&(e.textContent=je(p)),n&&(n.textContent=je(f)),a&&(a.textContent=je(M)),r&&(M>0?(r.style.display="",r.textContent=M):r.style.display="none"),o&&l){const I=l.ocr_this_month||0,x=l.quota||0;o.textContent=je(I),s&&(s.textContent=x?I+" / "+je(x)+" 张":Ce("dash-kpi-plan-sub","本月用量"))}if(i)if(b.length===0)i.innerHTML='<div class="dash-recent-empty">'+Ce("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>";else{const I=b.slice(0,5).map(x=>{const y=(x.invoice_no||x.filename||x.id||"").toString(),$=(x.supplier_name||x.buyer_name||x.client_name||x.notes||"").toString(),C=Ma(x.created_at||x.upload_time||x.date),F=j=>String(j).replace(/[&<>"']/g,_=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[_]);return'<div class="dash-recent-row"><span class="dash-recent-key" title="'+F(y)+'">'+F(y)+'</span><span class="dash-recent-mid" title="'+F($)+'">'+F($)+'</span><span class="dash-recent-time">'+F(C)+"</span></div>"}).join("");i.innerHTML=I}}catch{i&&(i.innerHTML='<div class="dash-recent-empty">'+Ce("dash-recent-empty","还没有识别记录 · 去上传第一张吧")+"</div>")}}window.loadDashboard=Et;async function an(){const e=document.getElementById("dash-kpi-balance-card"),n=document.getElementById("dash-kpi-usage-card"),a=document.getElementById("dash-kpi-balance"),o=document.getElementById("dash-kpi-balance-sub"),s=document.getElementById("dash-kpi-usage"),i=document.getElementById("dash-kpi-usage-sub");if(!(!e||!n))try{const r={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},u=await fetch("/api/me/credits",{headers:r,cache:"no-store"});if(!u.ok){e.style.display="none",s&&(s.textContent="—"),i&&(i.textContent="");return}const l=await u.json(),d=!!l.is_owner,c=!!l.is_billing_exempt;if(!d)e.style.display="none";else if(e.style.display="",c)a&&(a.textContent="∞",a.className="dash-kpi-val dash-green"),o&&(o.textContent=typeof window.t=="function"?window.t("dash-kpi-balance-exempt"):"Billing exempt");else{const f=typeof l.balance_thb=="number"?l.balance_thb:0;if(a&&(a.textContent="฿"+f.toFixed(2),a.className=f<50?"dash-kpi-val dash-red":"dash-kpi-val"),o){const m=typeof window.t=="function"?window.t("dash-kpi-balance-topup"):"Top up →",b=f<50?"#dc2626":"#6b7280",M=I=>typeof window.escapeHtml=="function"?window.escapeHtml(I):String(I).replace(/[&<>"']/g,x=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[x]);o.innerHTML='<a href="#" id="kpi-balance-topup-link" style="color:'+b+';text-decoration:underline;cursor:pointer;" onclick="event.preventDefault();window._openTopupModal&&window._openTopupModal();return false;">'+M(m)+"</a>"}}const p=typeof l.pages_this_month=="number"?l.pages_this_month:typeof l.my_invoice_count=="number"?l.my_invoice_count:0;if(n.style.display="",s&&(s.textContent=String(p)),i){const f=p>=200?"dash-kpi-usage-sub-high":"dash-kpi-usage-sub-low",m=typeof window.t=="function"?window.t(f,{used:p}):p+" pages";i.textContent=m}}catch(r){console.warn("[credits] loadCreditsCard failed:",r),e.style.display="none",s&&(s.textContent="—")}}window.loadCreditsCard=an;document.addEventListener("DOMContentLoaded",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&setTimeout(Et,500)});typeof window.subscribeI18n=="function"&&window.subscribeI18n("dashboard",function(){(location.hash||"").replace(/^#\//,"")==="dashboard"&&Et()});function he(e){return(typeof window.t=="function"?window.t(e):null)||e}function It(){return localStorage.getItem("mrpilot_token")||""}function ve(e){return document.getElementById(e)}var Ge=null,De=null;function on(){De||(De=setInterval(function(){if(!document.hidden){var e=It();e&&(window._userInfo&&window._userInfo.is_billing_exempt||fetch("/api/me/credits",{headers:{Authorization:"Bearer "+e},cache:"no-store"}).then(function(n){return n.ok?n.json():null}).then(function(n){if(n){var a=n.balance_thb!=null?Number(n.balance_thb):0;Ge!==null&&a>Ge&&(window.showToast&&window.showToast(he("credits-updated"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard(),typeof window._refreshBalanceAlerts=="function"&&window._refreshBalanceAlerts()),Ge=a}}).catch(function(){}))}},3e4))}function Ha(){De&&(clearInterval(De),De=null),Ge=null}window._startCreditsPoll=on;window._stopCreditsPoll=Ha;on();var Bt=null,Lt=0;function Aa(){if(!ve("topup-v2-ov")){var e=document.createElement("div");e.id="topup-v2-ov",e.className="topup-v2-ov",e.style.cssText="display:none;position:fixed;inset:0;background:rgba(15,23,42,.5);z-index:9500;align-items:center;justify-content:center;padding:16px",e.innerHTML=['<div class="topup-v2-box">','  <div class="topup-v2-head">','    <div class="topup-v2-title" id="tv2-title"></div>','    <button class="topup-v2-close" id="tv2-close" aria-label="close">','      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="4" x2="16" y2="16"/><line x1="16" y1="4" x2="4" y2="16"/></svg>',"    </button>","  </div>",'  <div class="topup-v2-steps">','    <div class="topup-v2-step" id="tv2-d1"><span class="topup-v2-dot">1</span><span class="topup-v2-slabel" id="tv2-sl1"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d2"><span class="topup-v2-dot">2</span><span class="topup-v2-slabel" id="tv2-sl2"></span></div>','    <div class="topup-v2-line"></div>','    <div class="topup-v2-step" id="tv2-d3"><span class="topup-v2-dot">3</span><span class="topup-v2-slabel" id="tv2-sl3"></span></div>',"  </div>",'  <div class="topup-v2-body">','    <div id="tv2-s1">','      <label class="topup-v2-label" id="tv2-al"></label>','      <div class="topup-v2-qamts">','        <button class="topup-v2-qamt" data-val="100">฿100</button>','        <button class="topup-v2-qamt" data-val="500">฿500</button>','        <button class="topup-v2-qamt" data-val="1000">฿1,000</button>','        <button class="topup-v2-qamt" data-val="2000">฿2,000</button>',"      </div>",'      <input id="tv2-amt" type="number" min="10" step="1" class="topup-v2-input" placeholder="฿ ...">','      <div id="tv2-ae" class="topup-v2-err" style="display:none"></div>',"    </div>",'    <div id="tv2-s2" style="display:none">','      <p class="topup-v2-bank-label" id="tv2-bl"></p>','      <div class="topup-v2-bank-card">','        <div class="topup-v2-bank-name">ธนาคาร กรุงเทพ</div>','        <div class="topup-v2-bank-branch">สาขาโชคชัย 4 ลาดพร้าว</div>','        <div class="topup-v2-bank-acct">230-0-91368-4</div>','        <div class="topup-v2-bank-holder">บจ. มิสเตอร์ อี อาร์ พี</div>','        <button class="topup-v2-copy" id="tv2-copy"></button>',"      </div>",'      <div class="topup-v2-warn" id="tv2-bn"></div>',"    </div>",'    <div id="tv2-s3" style="display:none">','      <div class="topup-v2-drop" id="tv2-drop">','        <input type="file" id="tv2-file" accept="image/*,.pdf" style="display:none">','        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>','        <span class="topup-v2-drop-text" id="tv2-dt"></span>',"      </div>",'      <div id="tv2-se" class="topup-v2-err" style="display:none"></div>','      <label class="topup-v2-label" id="tv2-pl"></label>','      <input id="tv2-payer" type="text" maxlength="200" class="topup-v2-input">','      <label class="topup-v2-label" id="tv2-nl"></label>','      <input id="tv2-note" type="text" maxlength="500" class="topup-v2-input">','      <div id="tv2-ue" class="topup-v2-err" style="display:none"></div>',"    </div>","  </div>",'  <div class="topup-v2-foot">','    <button class="btn btn-ghost" id="tv2-back" style="display:none"></button>','    <button class="btn btn-primary" id="tv2-next"></button>',"  </div>","</div>"].join(""),document.body.appendChild(e),ja()}}function sn(){var e=function(n,a){var o=ve(n);o&&(o.textContent=a)};e("tv2-title",he("topup-title")),e("tv2-sl1",he("topup-step1")),e("tv2-sl2",he("topup-step2")),e("tv2-sl3",he("topup-step3")),e("tv2-al",he("topup-amount-label")),e("tv2-bl",he("topup-bank-label")),e("tv2-copy",he("topup-copy-account")),e("tv2-dt",he("topup-slip-drop")),e("tv2-pl",he("topup-payer-label")),e("tv2-nl",he("topup-note-label"))}function Re(e){[1,2,3].forEach(function(s){var i=ve("tv2-s"+s);i&&(i.style.display=s===e?"":"none");var r=ve("tv2-d"+s);r&&r.classList.toggle("active",s<=e)});var n=ve("tv2-back"),a=ve("tv2-next");if(e===1?n&&(n.style.display="",n.textContent=he("topup-btn-cancel")):n&&(n.style.display="",n.textContent=he("topup-btn-back")),a&&(a.textContent=he(e===3?"topup-btn-submit":"topup-btn-next")),e===2){var o=ve("tv2-bn");o&&(o.innerHTML=he("topup-bank-note").replace("{amount}","<strong>฿"+Number(Lt).toLocaleString()+"</strong>"))}}function ht(){for(var e=1;e<=3;e++){var n=ve("tv2-s"+e);if(n&&n.style.display!=="none")return e}return 1}function We(e){var n=ve(e);n&&(n.textContent="",n.style.display="none")}function qe(e,n){var a=ve(e);a&&(a.textContent=n,a.style.display="")}function Ht(e){var n=ve("tv2-dt");n&&(n.textContent=e.name);var a=ve("tv2-drop");a&&a.classList.add("has-file"),We("tv2-se")}function ja(){var e=ve("topup-v2-ov");ve("tv2-close").addEventListener("click",Pe),e.addEventListener("click",function(i){i.target===e&&Pe()}),document.addEventListener("keydown",function(i){i.key==="Escape"&&e&&e.style.display!=="none"&&Pe()}),e.addEventListener("click",function(i){var r=i.target.closest(".topup-v2-qamt");if(r){e.querySelectorAll(".topup-v2-qamt").forEach(function(l){l.classList.remove("active")}),r.classList.add("active");var u=ve("tv2-amt");u&&(u.value=r.dataset.val,We("tv2-ae"))}});var n=ve("tv2-amt");n&&n.addEventListener("input",function(){e.querySelectorAll(".topup-v2-qamt").forEach(function(i){i.classList.remove("active")}),We("tv2-ae")});var a=ve("tv2-copy");a&&a.addEventListener("click",function(){navigator.clipboard&&navigator.clipboard.writeText("2300913684").then(function(){var i=a.textContent;a.textContent=he("topup-copied"),setTimeout(function(){a.textContent=i},1500)})});var o=ve("tv2-drop"),s=ve("tv2-file");o&&(o.addEventListener("click",function(){s&&s.click()}),o.addEventListener("dragover",function(i){i.preventDefault(),o.classList.add("drag-over")}),o.addEventListener("dragleave",function(){o.classList.remove("drag-over")}),o.addEventListener("drop",function(i){i.preventDefault(),o.classList.remove("drag-over");var r=i.dataTransfer&&i.dataTransfer.files[0];r&&Ht(r)})),s&&s.addEventListener("change",function(){s.files[0]&&Ht(s.files[0])}),ve("tv2-back").addEventListener("click",function(){var i=ht();if(i<=1){Pe();return}Re(i-1)}),ve("tv2-next").addEventListener("click",function(){var i=ht();i===1?Pa():i===2?Re(3):Da()})}async function Pa(){var e=ve("tv2-amt"),n=e?parseFloat(e.value):0;if(!n||n<10){qe("tv2-ae",he("topup-amount-invalid"));return}if(n>5e5){qe("tv2-ae",he("topup-amount-too-large"));return}Lt=n;var a=ve("tv2-next");a&&(a.disabled=!0,a.textContent="…");try{var o=await fetch("/api/credits/topup/request",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+It()},body:JSON.stringify({amount_thb:n})});if(!o.ok){var s=await o.text(),i=he("topup-submit-fail");try{var r=JSON.parse(s),u=r.detail;if(Array.isArray(u)&&u.length){var l=u[0]&&u[0].type||"";l.indexOf("less_than")>=0?i=he("topup-amount-too-large"):(l.indexOf("greater_than")>=0||l.indexOf("parsing")>=0)&&(i=he("topup-amount-invalid"))}else typeof u=="string"&&(i=u)}catch{}throw new Error(i)}var d=await o.json();Bt=d.request_id,Re(2)}catch(c){qe("tv2-ae",c.message||he("topup-submit-fail"))}finally{a&&(a.disabled=!1,a.textContent=he("topup-btn-next"))}}async function Da(){var e=ve("tv2-file");if(!e||!e.files||!e.files[0]){qe("tv2-se",he("topup-slip-required"));return}var n=ve("tv2-next");n&&(n.disabled=!0,n.textContent="…");try{var a=new FormData;a.append("file",e.files[0]);var o=ve("tv2-payer"),s=ve("tv2-note");o&&o.value.trim()&&a.append("payer_name",o.value.trim()),s&&s.value.trim()&&a.append("note",s.value.trim());var i=await fetch("/api/credits/topup/upload-slip/"+Bt,{method:"POST",headers:{Authorization:"Bearer "+It()},body:a});if(!i.ok)throw new Error(await i.text());var r=await i.json();r.auto_approved?(window.showToast&&window.showToast(he("topup-auto-approved"),"success"),typeof window.loadDashboard=="function"&&window.loadDashboard()):window.showToast&&window.showToast(he("topup-pending"),"info"),Pe()}catch(u){qe("tv2-ue",he("topup-upload-fail")+" · "+u.message),n&&(n.disabled=!1,n.textContent=he("topup-btn-submit"))}}function Pe(){var e=ve("topup-v2-ov");e&&(e.style.display="none"),typeof window.loadDashboard=="function"&&window.loadDashboard()}window._openTopupModal=function(){Aa(),Bt=null,Lt=0,["tv2-amt","tv2-payer","tv2-note"].forEach(function(a){var o=ve(a);o&&(o.value="")});var e=ve("tv2-file");e&&(e.value="");var n=ve("tv2-drop");n&&n.classList.remove("has-file","drag-over"),ve("topup-v2-ov").querySelectorAll(".topup-v2-qamt").forEach(function(a){a.classList.remove("active")}),["tv2-ae","tv2-se","tv2-ue"].forEach(function(a){We(a)}),sn(),Re(1),ve("topup-v2-ov").style.display="flex"};typeof window.subscribeI18n=="function"&&window.subscribeI18n("topup-v2",function(){var e=ve("topup-v2-ov");e&&e.style.display!=="none"&&e.style.display!==""&&(sn(),Re(ht()))});(function(){const e="v118.28.5",n="pearnly_tc_results_"+e,a=[{id:"A1",group:"A · 异常栏 page-head(BUG1)",desc:"手机宽度进异常栏 · 标题「异常栏」横排正常 · 不再每字一行"},{id:"A2",group:"A · 异常栏 page-head(BUG1)",desc:"副标题「所有被规则拦截的单据集中复核…」也横排正常 · 不竖排"},{id:"A3",group:"A · 异常栏 page-head(BUG1)",desc:"客户筛选下拉 + 刷新按钮换到新一行 · 不抢标题宽度"},{id:"B1",group:"B · 客户管理 page-head(BUG2)",desc:"手机宽度进客户管理 · 标题「客户管理」横排正常"},{id:"B2",group:"B · 客户管理 page-head(BUG2)",desc:"副标题「为每家客户单独归档发票…」横排正常 · 不竖排"},{id:"B3",group:"B · 客户管理 page-head(BUG2)",desc:"「+ 新建客户」按钮换到新一行 · 不挤标题"},{id:"C1",group:"C · 客户卡片(BUG3)",desc:"客户卡片「编辑 / 导出本月」按钮文字清晰 · 不被截断"},{id:"D1",group:"D · 历史表头(BUG4)",desc:"手机宽度进单据记录 · 表头「文件·发票号·供应商」/「金额」单行 · 不竖排"},{id:"D2",group:"D · 历史表头(BUG4)",desc:"行内 INV-TH-202605-1006 这种长发票号正常单行展示 · 不一字一行"},{id:"E1",group:"E · 对账切换器(BUG6)",desc:"手机宽度进对账中心 · 顶栏点「全部客户」chip · 下拉从右上角向下展开 · 右对齐 · 不贴左屏边"},{id:"E2",group:"E · 对账切换器(BUG6)",desc:"下拉宽度自适应屏幕 · 不超出屏幕右边"},{id:"F1",group:"F · 通用设置回归",desc:"设置 → 个人资料 · 没有「界面语言」4 按钮卡"},{id:"F2",group:"F · 通用设置回归",desc:"左侧 nav 顺序:账户 / 公司 / 工作流 / 系统 / 关于"},{id:"F3",group:"F · 通用设置回归",desc:"系统 → 通用设置 · 4 行下拉(语言/时区/日期/数字)· 改语言立即切语言 · 改其他保存后 F5 仍保留"},{id:"G1",group:"G · 移动端 settings(回归)",desc:"手机宽度设置 tabs 不重叠 · 按分组分行 · chip 风格"},{id:"H1",group:"H · 回归",desc:"OCR 上传识别 / 客户管理 / 异常栏 / 对账中心 / 测试中心 全部仍工作"},{id:"H2",group:"H · 回归",desc:"4 语切换没新增异常(测试中心异常日志「API 失败」过滤无新条目)"},{id:"I1",group:"I · 三档移动 viewport",desc:"iPhone SE 375 · 上述 BUG 1-6 都修了"},{id:"I2",group:"I · 三档移动 viewport",desc:"Galaxy S 360 · 上述 BUG 1-6 都修了"},{id:"I3",group:"I · 三档移动 viewport",desc:"iPhone 12 Pro 414 · 上述 BUG 1-6 都修了"}];let o={},s="all",i=!1,r=!1;function u(G,W,te){let re=typeof t=="function"?t(G):null;return(!re||re===G)&&(re=W),te&&Object.keys(te).forEach(function(H){re=String(re).replace("{"+H+"}",String(te[H]))}),re}function l(){try{const G=localStorage.getItem(n);o=G?JSON.parse(G):{},(typeof o!="object"||!o)&&(o={})}catch{o={}}}function d(){try{localStorage.setItem(n,JSON.stringify(o))}catch{}}function c(G){const W=new Date(G),te=function(re){return re<10?"0"+re:""+re};return te(W.getHours())+":"+te(W.getMinutes())+":"+te(W.getSeconds())}function p(G){return String(G??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function f(G,W){try{typeof showToast=="function"?showToast(G,W||"info"):alert(G)}catch{}}function m(G){try{navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(G).then(function(){f(u("tc-toast-copied","已复制到剪贴板"),"success")}).catch(function(){b(G)}):b(G)}catch{b(G)}}function b(G){try{const W=document.createElement("textarea");W.value=G,W.style.position="fixed",W.style.opacity="0",document.body.appendChild(W),W.select();const te=document.execCommand("copy");document.body.removeChild(W),f(te?u("tc-toast-copied","已复制"):u("tc-toast-copy-fail","复制失败"),te?"success":"error")}catch{f(u("tc-toast-copy-fail","复制失败"),"error")}}function M(){const G=document.getElementById("tc-account-chip"),W=document.getElementById("tc-progress-chip");if(G&&(G.textContent=_userInfo&&(_userInfo.email||_userInfo.username)||"—"),W){const te=a.length,re=a.filter(function(H){return o[H.id]}).length;W.textContent=re+" / "+te}}function I(){const G=document.getElementById("tc-checklist-body");if(!G)return;const W={};a.forEach(function(re){W[re.group]||(W[re.group]=[]),W[re.group].push(re)});const te=[];Object.keys(W).forEach(function(re){te.push('<div class="tc-checklist-group">'),te.push('<div class="tc-checklist-group-title">'+p(re)+"</div>"),W[re].forEach(function(H){const E=o[H.id]||"",g=E?"is-"+E:"";te.push('<div class="tc-check-item '+g+'" data-id="'+p(H.id)+'"><div class="tc-check-id">'+p(H.id)+'</div><div class="tc-check-desc">'+p(H.desc)+'</div><div class="tc-check-actions">'+x(H.id,"pass",E)+x(H.id,"fail",E)+x(H.id,"skip",E)+"</div></div>")}),te.push("</div>")}),G.innerHTML=te.join("")}function x(G,W,te){const re=te===W,H={pass:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,11 8,15 16,5"/></svg>',fail:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="5" x2="15" y2="15"/><line x1="15" y1="5" x2="5" y2="15"/></svg>',skip:'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="10" x2="15" y2="10"/></svg>'},E={pass:u("tc-status-pass","通过"),fail:u("tc-status-fail","失败"),skip:u("tc-status-skip","跳过")};return'<button type="button" class="tc-status-btn '+(re?"is-active "+W:"")+'" data-id="'+p(G)+'" data-kind="'+W+'" title="'+p(E[W])+'">'+H[W]+"</button>"}function y(G){return s==="all"?!0:s==="js_error"?G.type==="js_error"||G.type==="promise_error":s==="api"?G.type==="api_error"||G.type==="api_fail":s==="api_slow"?G.type==="api_slow":s==="console"?G.type==="console_error"||G.type==="console_warn":!0}function $(){const G=document.getElementById("tc-logs-body"),W=document.getElementById("tc-logs-count");if(!G)return;const te=(window._pearnlyTcLogs||[]).slice().reverse(),re=te.filter(y);if(W&&(W.textContent=String(te.length)),re.length===0){G.innerHTML='<div class="tc-logs-empty">'+p(u("tc-logs-empty","暂无异常"))+"</div>";return}const H=re.slice(0,100).map(function(E){const g=typeof E.detail=="object"?JSON.stringify(E.detail,null,2):String(E.detail||"");return'<div class="tc-log-item t-'+p(E.type)+'" data-ts="'+E.ts+'"><span class="tc-log-time">'+c(E.ts)+'</span><span class="tc-log-type">'+p(E.type)+'</span><div class="tc-log-summary">'+p(E.summary)+'<div class="tc-log-detail">'+p(g)+"</div></div></div>"}).join("");G.innerHTML=H,document.querySelectorAll("#tc-logs-filter .tc-filter-chip").forEach(function(E){E.classList.toggle("active",E.getAttribute("data-filter")===s)})}function C(){r||(r=!0,setTimeout(function(){r=!1,currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&$(),F()},200))}window._tcOnNewLog=C;function F(){const G=document.getElementById("nav-test-badge");if(!G)return;const W=(window._pearnlyTcLogs||[]).filter(function(te){return te.type==="js_error"||te.type==="promise_error"||te.type==="api_error"||te.type==="api_fail"||te.type==="console_error"}).length;W>0?(G.style.display="",G.textContent=W>99?"99+":String(W)):G.style.display="none"}function j(){M(),I(),$(),F()}function _(){const G=[],W=new Date,te=_userInfo&&(_userInfo.email||_userInfo.username)||"—";G.push("# Pearnly "+e+" 测试结果"),G.push("- 账号:"+te),G.push("- 时间:"+W.toISOString().replace("T"," ").slice(0,19));const re=a.length,H=a.filter(function(Z){return o[Z.id]==="pass"}).length,E=a.filter(function(Z){return o[Z.id]==="fail"}).length,g=a.filter(function(Z){return o[Z.id]==="skip"}).length,q=re-H-E-g;G.push("- 进度:"+(H+E+g)+" / "+re+" · ✅ "+H+" · ❌ "+E+" · ⏭ "+g+" · 未测 "+q),G.push(""),G.push("| ID | 描述 | 状态 |"),G.push("|---|---|---|"),a.forEach(function(Z){const le=o[Z.id],ie=le==="pass"?"✅":le==="fail"?"❌":le==="skip"?"⏭":"⬜";G.push("| "+Z.id+" | "+Z.desc.replace(/\|/g,"\\|")+" | "+ie+" |")});const N=a.filter(function(Z){return o[Z.id]==="fail"});N.length>0&&(G.push(""),G.push("## ❌ 失败项"),N.forEach(function(Z){G.push("- **"+Z.id+"** · "+Z.desc)}));const K=(window._pearnlyTcLogs||[]).slice(-30).reverse();return K.length>0&&(G.push(""),G.push("## 🔴 异常日志(最近 "+K.length+" 条)"),K.forEach(function(Z){if(G.push("- `"+c(Z.ts)+"` · **"+Z.type+"** · "+Z.summary),Z.detail){let le;try{le=JSON.stringify(Z.detail)}catch{le=String(Z.detail)}le&&le!=="{}"&&G.push("  - "+le.slice(0,600))}})),G.join(`
`)}function h(G){const W=(window._pearnlyTcLogs||[]).slice(-30).reverse();if(W.length===0)return"(暂无异常日志)";const te=["# Pearnly 异常日志(最近 "+W.length+" 条)"],re=_userInfo&&(_userInfo.email||_userInfo.username)||"—";return te.push("- 账号:"+re),te.push("- 当前页:"+(currentRoute||"?")),te.push("- UA:"+navigator.userAgent),te.push(""),W.forEach(function(H){if(te.push("## `"+c(H.ts)+"` · "+H.type),te.push("- "+H.summary),H.detail){te.push("```");try{te.push(JSON.stringify(H.detail,null,2).slice(0,2e3))}catch{te.push(String(H.detail).slice(0,2e3))}te.push("```")}}),te.join(`
`)}function w(){const G=Date.now();fetch("/api/health").then(function(W){const te=Date.now()-G;W.ok?f(u("tc-toast-health-ok","后端健康 ✓ {ms}ms",{ms:te}),"success"):f(u("tc-toast-health-fail","后端无响应")+" ("+W.status+")","error")}).catch(function(){f(u("tc-toast-health-fail","后端无响应"),"error")})}function L(){try{localStorage.removeItem(n),localStorage.removeItem("pearnly_current_client_id"),o={},(window._pearnlyTcLogs||[]).length=0,s="all",window.setCurrentClientId}catch{}j(),f(u("tc-toast-cleared","session 状态已清空"),"success")}function S(){try{fetch("/api/clients",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}).then(function(G){return G.json()}).then(function(G){window._clientsCache=G.clients||[],typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher(),typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter(),f("客户缓存已刷新 · "+(G.clients||[]).length+" 个客户","success")}).catch(function(){f("刷新失败","error")})}catch{}}function D(){if(i||!document.getElementById("page-test-center"))return;i=!0;const W=document.getElementById("tc-checklist-body");W&&W.addEventListener("click",function(le){const ie=le.target.closest(".tc-status-btn");if(!ie)return;const V=ie.getAttribute("data-id"),Q=ie.getAttribute("data-kind");!V||!Q||(o[V]===Q?delete o[V]:o[V]=Q,d(),I(),M())});const te=document.getElementById("tc-btn-reset-checklist");te&&te.addEventListener("click",function(){o={},d(),I(),M()});const re=document.getElementById("tc-btn-copy-all");re&&re.addEventListener("click",function(){m(_())});const H=document.getElementById("tc-btn-copy-logs");H&&H.addEventListener("click",function(){m(h())});const E=document.getElementById("tc-btn-clear-logs");E&&E.addEventListener("click",function(){(window._pearnlyTcLogs||[]).length=0,$(),F()});const g=document.getElementById("tc-logs-filter");g&&g.addEventListener("click",function(le){const ie=le.target.closest(".tc-filter-chip");ie&&(s=ie.getAttribute("data-filter")||"all",$())});const q=document.getElementById("tc-logs-body");q&&q.addEventListener("click",function(le){const ie=le.target.closest(".tc-log-item");ie&&ie.classList.toggle("expanded")});const N=document.getElementById("tc-tool-health");N&&N.addEventListener("click",w);const K=document.getElementById("tc-tool-clear-session");K&&K.addEventListener("click",L);const Z=document.getElementById("tc-tool-reload-clients");Z&&Z.addEventListener("click",S)}function B(){}window._tcApplyVisibility=B;let P=0;const Y=setInterval(function(){P++,_userInfo&&clearInterval(Y),P>60&&clearInterval(Y)},500);window.loadTestCenterPage=function(){l(),D(),j()},typeof window.subscribeI18n=="function"&&window.subscribeI18n("test-center",function(){F(),currentRoute==="test-center"&&document.getElementById("page-test-center")&&document.getElementById("page-test-center").classList.contains("active")&&j()})})();(function(){const e="pearnly_active_workspace_client_id",n="pearnly_work_mode";function a(y,$){if(typeof window.t=="function"){const C=window.t(y);if(C&&C!==y)return C}return $}function o(){const y=window._userInfo||{},$=String(y.role||"").toLowerCase(),C=String(y.tenant_role||"").toLowerCase();return y.is_super_admin===!0||y.is_owner===!0||$==="owner"||$==="admin"||C==="owner"||C==="admin"}function s(){return localStorage.getItem(n)==="client"?"client":"personal"}function i(){const y=localStorage.getItem(e);if(!y||y==="null"||y==="0"||y==="")return null;const $=parseInt(y,10);return isNaN($)?null:$}function r(y){try{window.dispatchEvent(new CustomEvent("pearnly:workspace-changed",{detail:{id:y,mode:s()}}))}catch{}}function u(y){const $=i();y==null||y===0?localStorage.removeItem(e):(localStorage.setItem(e,String(y)),localStorage.setItem(n,"client")),String($)!==String(y)&&r(y)}function l(){const y=i();localStorage.setItem(n,"personal"),localStorage.removeItem(e),y!=null&&r(null)}async function d(){try{const y=window.apiGet;if(typeof y!="function")return[];const $=await y("/api/workspace/clients");return $&&($.clients||$.items)||[]}catch{return[]}}async function c(y){if(s()==="client"&&i()!=null)return typeof y=="function"&&y(),!0;const $=a("ws-need-client","这个功能需要先选择工作空间"),C=a("ws-btn-pick","选择工作空间"),F=a("ws-btn-cancel","取消");return typeof window.showConfirm=="function"?await window.showConfirm($,{okText:C,cancelText:F})&&p(y):window.confirm($+`

[`+C+" / "+F+"]")&&p(y),!1}async function p(y){const $=await d();if(typeof y=="function"&&s()!=="personal"&&$.length===1){u(Number($[0].id)),y();return}if(typeof window.openWorkspaceChooserUI=="function"){window.openWorkspaceChooserUI({clients:$,canCreate:o(),active:i(),onPersonal:l,onPick:function(C){u(Number(C)),typeof y=="function"&&y()},emptyHint:$.length?null:o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。")});return}if(!$.length){const C=o()?a("ws-empty-owner","还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。"):a("ws-empty-employee","你还没有可用的工作空间,请联系管理员分配。");typeof window.showToast=="function"&&window.showToast(C,"info")}}function f(y){const $=y||document.getElementById("workspace-switcher-root");if(!$)return;const C=s(),F=i();let j,_;if(C==="client"&&F!=null){const L=(window._workspaceClientsCache||[]).find(S=>Number(S.id)===Number(F));j=b("building"),_=L?L.name:a("ws-current-label","当前工作空间")}else j=b("user"),_=a("ws-personal","个人事务");$.innerHTML='<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">'+j+'<span class="ws-ctrl-label">'+m(_)+"</span></button>";const h=$.querySelector("#ws-ctrl-btn");h&&h.addEventListener("click",()=>p(null))}function m(y){return String(y??"").replace(/[&<>"']/g,function($){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[$]})}function b(y){const $='<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';return y==="building"?$+'<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>':$+'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'}function M(y){y=y||{};const $=y.clients||[],C=y.active,F=document.getElementById("ws-modal");F&&F.remove();const j=document.createElement("div");j.id="ws-modal",j.className="ws-modal";const h='<button type="button" class="ws-modal-item'+(s()==="personal"||C==null?" active":"")+'" data-ws-personal="1"><span class="ws-modal-item-ic">'+b("user")+'</span><span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;"><span class="ws-modal-item-name">'+m(a("ws-personal","个人事务"))+'</span><span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">'+m(a("ws-personal-desc","用于临时识别、测试或处理不归属任何公司的文件。"))+"</span></span></button>";let w="";if($.length){const P=['<option value="">'+m(a("ws-select-ph","— 选择账套主体 —"))+"</option>"].concat($.map(function(Y){const G=C!=null&&Number(C)===Number(Y.id);return'<option value="'+m(Y.id)+'"'+(G?" selected":"")+">"+m(Y.name||"#"+Y.id)+"</option>"}));w='<div class="ws-modal-select-row"><label class="ws-modal-select-label">'+m(a("ws-select-label","账套主体"))+'</label><select class="ws-modal-select" data-ws-select="1">'+P.join("")+"</select></div>"}const L=!$.length&&y.emptyHint?'<div class="ws-modal-empty">'+m(y.emptyHint)+"</div>":"",S=y.canCreate?'<div class="ws-modal-create"><button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ '+m(a("ws-create-client","新建工作空间"))+'</button><div class="ws-modal-create-form" data-ws-create-form style="display:none;"><input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="'+m(a("ws-create-ph","公司名称,例如 BAKELAB"))+'"><button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">'+m(a("ws-create-submit","创建"))+"</button></div></div>":"";j.innerHTML='<div class="ws-modal-box" role="dialog" aria-modal="true"><div class="ws-modal-head"><span class="ws-modal-title">'+m(a("ws-chooser-title","选择工作空间"))+'</span><button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button></div><div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">'+m(a("ws-chooser-subtitle","账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。"))+'</div><div class="ws-modal-list">'+h+w+"</div>"+L+S+"</div>",document.body.appendChild(j);const D=j.querySelector("[data-ws-select]");D&&D.addEventListener("change",function(){const P=D.value;P&&(typeof y.onPick=="function"&&y.onPick(P),B(),f())});function B(){j.remove()}j.addEventListener("click",function(P){if(P.target===j||P.target.closest("[data-ws-close]")){B();return}if(P.target.closest("[data-ws-personal]")){typeof y.onPersonal=="function"&&y.onPersonal(),B(),f();return}const G=P.target.closest("[data-ws-pick]");if(G){const re=G.getAttribute("data-ws-pick");typeof y.onPick=="function"&&y.onPick(re),B(),f();return}if(P.target.closest("[data-ws-create-toggle]")){const re=j.querySelector("[data-ws-create-form]");if(re){re.style.display=re.style.display==="none"?"flex":"none";const H=re.querySelector("[data-ws-create-name]");H&&H.focus()}return}if(P.target.closest("[data-ws-create-submit]")){I(j,y,B);return}})}async function I(y,$,C){const F=y.querySelector("[data-ws-create-name]"),j=F?(F.value||"").trim():"";if(!j){F&&F.focus();return}let _=null;try{if(typeof window.apiPost=="function"){const w=await window.apiPost("/api/workspace/clients",{name:j});_=w&&typeof w.json=="function"?await w.json().catch(()=>null):w}}catch{_=null}const h=_&&(_.id||_.client&&_.client.id);if(!h){typeof window.showToast=="function"&&window.showToast(a("ws-create-fail","新建工作空间失败 · 请重试"),"error");return}window._workspaceClientsCache=await d(),u(Number(h)),$.onPick,C(),f()}window.openWorkspaceChooserUI=M,window.addEventListener("pearnly:workspace-changed",function(){f()}),window.getWorkMode=s,window.getActiveWorkspaceClientId=i,window.setActiveWorkspaceClientId=u,window.enterPersonalMode=l,window.requireWorkspace=c,window.openWorkspaceChooser=p,window.renderWorkspaceControl=f,window.fetchWorkspaceClients=d;function x(){try{if(sessionStorage.getItem("pearnly_ws_login_prompted")==="1"||i()!=null||localStorage.getItem(n)==="personal")return;sessionStorage.setItem("pearnly_ws_login_prompted","1"),setTimeout(function(){p(null)},800)}catch{}}d().then(y=>{window._workspaceClientsCache=y,f(),x()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("workspace-switcher",f)})();(function(){const e=C=>document.querySelector('[data-num-target="'+C+'"]');function n(C){if(!C)return t("reconcile-last-activity-none");try{const F=new Date(C),j=new Date,_=j-F;if(_/6e4<5)return t("reconcile-last-activity-just-now");if(F.toDateString()===j.toDateString())return t("reconcile-last-activity-today");const w=Math.max(1,Math.floor(_/(24*3600*1e3)));return t("reconcile-last-activity-days-ago").replace("{n}",w)}catch{return t("reconcile-last-activity-none")}}function a(C,F,j){const _=e(C);_&&(_.textContent=j?"-":String(F),_.classList.toggle("is-empty",!!j))}function o(C){const F=document.getElementById("reconcile-error");F&&(F.style.display=C?"flex":"none")}function s(C){const F=document.getElementById("reconcile-empty");F&&(F.style.display=C?"flex":"none")}function i(C,F){const j=document.getElementById("reconcile-last-activity");j&&(j.textContent=C,j.classList.toggle("has-data",!!F))}function r(C){const F=!C||(C.total_sessions||0)===0;a("pending",C.pending||0,F),a("matched",C.matched||0,F),a("unmatched",C.unmatched||0,F),i(n(C.last_activity_at),!!C.last_activity_at),o(!1),s(F)}function u(C){const F=C.toUpperCase();return F==="KBANK"?"bank-chip-kbank":F==="SCB"?"bank-chip-scb":F==="BBL"?"bank-chip-bbl":F==="KTB"?"bank-chip-ktb":F==="TTB"?"bank-chip-ttb":"bank-chip-other"}function l(C,F){const j=_=>_?String(_).slice(0,10):"?";return!C&&!F?"":j(C)+" ~ "+j(F)}function d(C){return C==null?"":String(C).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function c(C){const F=document.getElementById("reconcile-recent"),j=document.getElementById("reconcile-recent-list");if(!F||!j)return;const _=(C||[]).slice(0,20);if(_.length===0){F.style.display="none";return}F.style.display="",s(!1),j.innerHTML=_.map(h=>{const w=h.parse_status==="parse_failed",L=h.bank_code||"OTHER",S=h.account_last4?" ···"+d(h.account_last4):"",D=l(h.period_start,h.period_end),B=d(h.source_filename||""),P=Number(h.tx_count||0),Y=w?'<span class="recon-card-fail" data-i18n="reconcile-card-parse-failed">'+t("reconcile-card-parse-failed")+"</span>":'<span class="recon-card-tx">'+t("reconcile-card-tx").replace("{n}",P)+"</span>";return'<div class="recon-card" data-session-id="'+d(h.id)+'" data-session-name="'+B+'"><span class="bank-chip '+u(L)+'">'+d(L)+'</span><div class="recon-card-main"><div class="recon-card-title">'+B+S+'</div><div class="recon-card-sub">'+d(D)+'</div></div><div class="recon-card-right">'+Y+'</div><button class="recon-card-trash" data-trash="'+d(h.id)+'" title="'+d(t("bank-session-delete-tip")||"删除")+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg></button><svg class="recon-card-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg></div>'}).join(""),j.querySelectorAll(".recon-card").forEach(h=>{h.addEventListener("click",w=>{w.target.closest(".recon-card-trash")||(h.dataset.sessionId,p())})}),j.querySelectorAll(".recon-card-trash").forEach(h=>{h.addEventListener("click",w=>{w.stopPropagation();const L=h.dataset.trash,S=h.closest(".recon-card"),D=S&&S.dataset.sessionName||"";typeof window._deleteBankSession=="function"&&window._deleteBankSession(L,D)})})}function p(C){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const F=document.querySelector('[data-recon-tab="bank"]');F&&F.click()},150)}function f(){o(!0),s(!1)}function m(){typeof window.routeTo=="function"&&window.routeTo("reconcile"),setTimeout(function(){const C=document.querySelector('[data-recon-tab="bank"]');C&&C.click()},150)}async function b(){a("pending",0,!0),a("matched",0,!0),a("unmatched",0,!0),i("",!1),o(!1),s(!1);const C=document.getElementById("reconcile-recent");C&&(C.style.display="none");const F={Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")};try{const[j,_]=await Promise.all([fetch("/api/bank-recon/stats",{headers:F}),fetch("/api/bank-recon/sessions?limit=20",{headers:F})]);if(!j.ok)throw new Error("http "+j.status);const h=await j.json(),w=_.ok?await _.json():[];r(h||{}),c(w||[])}catch(j){console.warn("[reconcile] load failed",j),f()}}function M(C){if(!C||!C.length)return;const F="Bearer "+(localStorage.getItem("mrpilot_token")||"");let j=0;const _=C.length;Array.from(C).forEach(function(h){const w=new FormData;w.append("file",h,h.name);const L=new XMLHttpRequest;L.open("POST","/api/bank-recon/upload"),L.setRequestHeader("Authorization",F),L.onload=function(){j++;try{const S=JSON.parse(L.responseText);L.status===200&&S.tx_count!==void 0?showToast((t("bank-upload-ok")||"解析成功 · 共 {n} 条流水").replace("{n}",S.tx_count),"success"):showToast(h.name+" "+(t("upload-failed")||"上传失败"),"error")}catch{showToast(h.name+" "+(t("upload-failed")||"上传失败"),"error")}j===_&&setTimeout(b,600)},L.onerror=function(){j++,showToast(h.name+" "+(t("upload-failed")||"上传失败"),"error"),j===_&&setTimeout(b,600)},L.send(w)}),showToast((t("bank-queue-status-uploading")||"上传中")+"…","info")}function I(){if(window.__reconcileBound)return;window.__reconcileBound=!0;const C=document.getElementById("reconcile-bank-file-input");C&&C.addEventListener("change",function(){M(this.files),this.value=""}),document.addEventListener("click",F=>{if(F.target.closest("#btn-reconcile-upload-top")||F.target.closest("#btn-reconcile-upload-empty")){m();return}if(F.target.closest("#btn-reconcile-retry")){b();return}if(F.target.closest("#btn-reconcile-dev-seed")){$();return}})}const x=["468b50c1-5593-4fd6-990d-515ce8085563"];function y(){const C=document.getElementById("btn-reconcile-dev-seed");if(!C)return;const F=typeof _userInfo<"u"?_userInfo:null,j=F&&F.id&&x.indexOf(String(F.id))>=0;C.style.display=j?"":"none"}async function $(){try{const C=await fetch("/api/bank-recon/_dev/seed",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!C.ok)throw new Error("seed:"+C.status);const F=await C.json(),j=(t("reconcile-dev-seed-ok")||"").replace("{n}",F.tx_count||0);showToast(j,"success"),typeof window.navigateTo=="function"?window.navigateTo("automation"):location.hash="#/automation",setTimeout(()=>{const _=document.querySelector('[data-auto-tab="bank"]');_&&_.click(),F.session_id&&typeof window._openBankSession=="function"&&window._openBankSession(F.session_id)},300)}catch(C){console.warn("[reconcile] dev seed failed",C),showToast(t("reconcile-dev-seed-fail")||"Seed failed","error")}}window.loadReconcilePage=async function(){I(),y(),typeof window._bankReconV2Init=="function"&&window._bankReconV2Init();try{await b()}catch{}},window._rerenderReconcile=function(){typeof currentRoute=="string"&&currentRoute==="reconcile"&&b().catch(()=>{})},typeof window.subscribeI18n=="function"&&window.subscribeI18n("reconcile",window._rerenderReconcile)})();(function(){const e=document.getElementById("assign-clients-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
    </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e={employeeId:null,employeeName:"",clients:[],selected:new Set,opened:!1};function n(){return document.getElementById("assign-clients-modal")}function a(){return document.getElementById("assign-clients-list")}function o(){return document.getElementById("assign-select-all")}function s(){return document.getElementById("assign-selected-count")}function i(){return document.getElementById("assign-modal-target")}function r(){const b=a();if(b){if(!e.clients.length){b.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-no-clients")||"暂无客户 · 请先到「客户管理」添加")+"</div>";return}b.innerHTML=e.clients.map(M=>{const I=String(M.id),x=e.selected.has(I)?"checked":"",y=escapeHtml(M.name||M.label||"#"+I),$=M.code?'<span class="assign-row-code">'+escapeHtml(M.code)+"</span>":"";return'<label class="assign-row"><input type="checkbox" data-cid="'+escapeHtml(I)+'" '+x+'><span class="assign-row-name">'+y+"</span>"+$+"</label>"}).join(""),u()}}function u(){const b=s();if(b){const I=t("assign-selected-count")||"已选 {n} / {total}";b.textContent=I.replace("{n}",e.selected.size).replace("{total}",e.clients.length)}const M=o();M&&(M.checked=e.clients.length>0&&e.selected.size===e.clients.length)}function l(){const b=i();b&&(b.textContent=e.employeeName?" · "+e.employeeName:"")}async function d(b,M){e.employeeId=b,e.employeeName=M||"",e.opened=!0,e.selected=new Set,e.clients=[],l();const I=a();I&&(I.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-loading")||"加载中...")+"</div>");const x=n();x&&(x.style.display="flex");try{const[y,$]=await Promise.all([apiGet("/api/clients?include_inactive=false"),apiGet("/api/team/employees/"+encodeURIComponent(b)+"/assignments")]);e.clients=y&&y.clients||[];const C=$&&$.client_ids||[];e.selected=new Set(C.map(String)),r()}catch(y){console.error("[assign-clients] load failed",y);const $=a();$&&($.innerHTML='<div class="assign-empty">'+escapeHtml(t("assign-load-failed")||"加载失败 · 请重试")+"</div>")}}function c(){e.opened=!1;const b=n();b&&(b.style.display="none")}async function p(){if(!e.employeeId)return;const b=Array.from(e.selected).map(I=>parseInt(I,10)).filter(I=>!isNaN(I)),M=document.getElementById("assign-modal-save");M&&(M.disabled=!0);try{const I=await apiPost("/api/team/employees/"+encodeURIComponent(e.employeeId)+"/assignments",{client_ids:b});I&&I.ok!==!1?(showToast((t("assign-saved")||"已保存 {n} 个客户分配").replace("{n}",b.length),"success"),c(),typeof loadTeamList=="function"&&loadTeamList()):showToast(t("assign-save-failed")||"保存失败","error")}catch(I){console.error("[assign-clients] save failed",I),showToast(t("assign-save-failed")||"保存失败","error")}finally{M&&(M.disabled=!1)}}function f(){const b=n();if(!b||b.dataset.bound==="1")return;b.dataset.bound="1";const M=document.getElementById("assign-modal-close");M&&M.addEventListener("click",c);const I=document.getElementById("assign-modal-cancel");I&&I.addEventListener("click",c);const x=document.getElementById("assign-modal-save");x&&x.addEventListener("click",p),b.addEventListener("click",function(C){C.target===b&&c()});const y=o();y&&y.addEventListener("change",function(){y.checked?e.selected=new Set(e.clients.map(C=>String(C.id))):e.selected=new Set,r()});const $=a();$&&$.addEventListener("change",function(C){const F=C.target.closest('input[type="checkbox"][data-cid]');if(!F)return;const j=F.dataset.cid;F.checked?e.selected.add(j):e.selected.delete(j),u()})}function m(){e.opened&&(l(),r())}typeof window.subscribeI18n=="function"&&window.subscribeI18n("assign-clients-modal",m),window.openAssignClientsModal=function(b,M){f(),d(b,M)}})();(function(){const e={page:1,per_page:50,q:"",total:0,rows:[],loaded:!1};function n(c){if(!c)return"";try{return new Date(c).toLocaleString()}catch{return c}}function a(c){const p=document.getElementById("access-log-table");p&&(p.innerHTML='<div class="access-log-empty">'+escapeHtml(c)+"</div>");const f=document.getElementById("access-log-pager");f&&(f.innerHTML="")}function o(){const c=document.getElementById("access-log-table");if(!c)return;const p=e.rows||[];if(!p.length){a(t("set-access-log-empty"));return}const f=`
            <div class="access-log-row access-log-head">
                <div>${escapeHtml(t("set-access-log-col-time"))}</div>
                <div>${escapeHtml(t("set-access-log-col-actor"))}</div>
                <div>${escapeHtml(t("set-access-log-col-action"))}</div>
                <div>${escapeHtml(t("set-access-log-col-target"))}</div>
                <div>${escapeHtml(t("set-access-log-col-ip"))}</div>
            </div>`,m=p.map(function(b){return`
                <div class="access-log-row">
                    <div class="access-log-time" data-label="${escapeHtml(t("set-access-log-col-time"))}">${escapeHtml(n(b.created_at))}</div>
                    <div class="access-log-actor" data-label="${escapeHtml(t("set-access-log-col-actor"))}">${escapeHtml(b.actor_username||"-")}</div>
                    <div data-label="${escapeHtml(t("set-access-log-col-action"))}"><span class="access-log-action">${escapeHtml(b.action||"-")}</span></div>
                    <div class="access-log-target" data-label="${escapeHtml(t("set-access-log-col-target"))}">${escapeHtml(b.target_name||b.target_type||"-")}</div>
                    <div class="access-log-ip" data-label="${escapeHtml(t("set-access-log-col-ip"))}">${escapeHtml(b.ip||"-")}</div>
                </div>`}).join("");c.innerHTML=f+m}function s(){const c=document.getElementById("access-log-pager");if(!c)return;const p=e.total||0;if(!p){c.innerHTML="";return}const f=e.page||1,m=e.per_page,b=Math.max(1,Math.ceil(p/m)),M=(t("set-access-log-pager-total")||"Total {n}").replace("{n}",p),I=(t("set-access-log-pager-page")||"Page {p} / {t}").replace("{p}",f).replace("{t}",b);c.innerHTML=`
            <div class="access-log-pager-info">${escapeHtml(M)}</div>
            <div class="access-log-pager-ctrl">
                <button class="access-log-pager-btn" type="button" data-access-log-page="${f-1}" ${f<=1?"disabled":""}>← ${escapeHtml(t("set-access-log-pager-prev"))}</button>
                <span class="access-log-pager-page">${escapeHtml(I)}</span>
                <button class="access-log-pager-btn" type="button" data-access-log-page="${f+1}" ${f>=b?"disabled":""}>${escapeHtml(t("set-access-log-pager-next"))} →</button>
            </div>`}async function i(c){const p=localStorage.getItem("mrpilot_token");if(p){e.page=c||1,a(t("set-access-log-loading"));try{const f="/api/me/access_log?page="+e.page+"&per_page="+e.per_page+"&q="+encodeURIComponent(e.q||""),m=await fetch(f,{headers:{Authorization:"Bearer "+p}});if(m.status===403){a(t("set-access-log-empty"));return}if(!m.ok)throw new Error("http_"+m.status);const b=await m.json();e.rows=b.logs||[],e.total=b.total||0,e.loaded=!0,o(),s()}catch{a(t("set-access-log-fail"))}}}async function r(){const c=localStorage.getItem("mrpilot_token");if(c)try{const p="/api/me/access_log.csv?q="+encodeURIComponent(e.q||""),f=await fetch(p,{headers:{Authorization:"Bearer "+c}});if(!f.ok){showToast(t("set-access-log-csv-fail")||"Export failed","error");return}const m=await f.blob(),b=document.createElement("a"),M=URL.createObjectURL(m);b.href=M,b.download="pearnly_access_log.csv",document.body.appendChild(b),b.click(),setTimeout(function(){URL.revokeObjectURL(M),b.remove()},100),showToast(t("set-access-log-csv-ok")||"Exported","success")}catch{showToast(t("set-access-log-csv-fail")||"Export failed","error")}}function u(){const c=document.querySelectorAll(".set-tab-owner-only"),p=!!(_userInfo&&(_userInfo.role==="owner"||_userInfo.is_super_admin));c.forEach(function(f){f.style.display=p?"":"none"})}document.addEventListener("click",function(c){if(c.target.closest('.settings-tab[data-tab="access-log"]')){setTimeout(function(){(!e.loaded||e.page!==1)&&i(1)},50);return}if(c.target.closest("#access-log-csv-btn")){c.preventDefault(),r();return}const m=c.target.closest(".access-log-pager-btn[data-access-log-page]");if(m&&!m.disabled){const b=parseInt(m.dataset.accessLogPage,10);i(b)}}),document.addEventListener("input",function(c){c.target&&c.target.id==="access-log-search"&&(clearTimeout(window.__accessLogSearchTimer),window.__accessLogSearchTimer=setTimeout(function(){e.q=(c.target.value||"").trim(),i(1)},350))});let l=0;const d=setInterval(function(){l++,_userInfo&&(u(),clearInterval(d)),l>60&&clearInterval(d)},500);typeof window.subscribeI18n=="function"&&window.subscribeI18n("me-access-log",function(){u(),e.loaded&&(o(),s())})})();(function(){const e=document.getElementById("notif-new-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){const e=j=>document.getElementById(j);async function n(j,_){return await fetch(j,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(_||{})})}async function a(j){return await fetch(j,{method:"DELETE",headers:{Authorization:"Bearer "+token}})}let o=null;async function s(){try{o=await apiGet("/api/line/binding")}catch{o={bound:!1}}return o}function i(j,_){if(!j)return;j.style.display="",j.className="notif-line-check "+(_?"bound":"unbound");const h=_?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>';j.innerHTML=h+"<span>"+escapeHtml(t(_?"notif-line-bound":"notif-line-not-bound"))+"</span>"}function r(j){if(j==null)return"-";const _=Number(j);return isNaN(_)?String(j):"฿ "+_.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function u(j){if(!j)return"-";try{const _=new Date(j),h=(_.getMonth()+1).toString().padStart(2,"0"),w=_.getDate().toString().padStart(2,"0"),L=_.getHours().toString().padStart(2,"0"),S=_.getMinutes().toString().padStart(2,"0");return`${h}-${w} ${L}:${S}`}catch{return j}}function l(j){const _=e("notif-rules-list"),h=e("notif-rules-empty"),w=e("notif-rules-count");if(!(!_||!h)){if(w.textContent=String(j.length),w.className="auto-status-pill "+(j.length>0?"active":"none"),!j.length){h.style.display="",_.style.display="none",_.innerHTML="";return}h.style.display="none",_.style.display="",_.innerHTML=j.map(L=>{const S=L.template_code==="large_invoice",D=S?"notif-rule-large-tag":"notif-rule-exception-tag",B=S?"large":"";let P=[];if(S){const G=L.params&&L.params.threshold?r(L.params.threshold):"-";P.push(escapeHtml(t("notif-rule-threshold-prefix"))+" "+G)}L.enabled||P.push('<span style="color:#9ca3af;">'+escapeHtml(t("notif-rule-disabled"))+"</span>");const Y=P.length?P.join(' <span class="dot"></span> '):"";return`
                <div class="notif-rule-row${L.enabled?"":" disabled"}" data-rule-id="${L.id}">
                    <span class="notif-rule-tmpl-badge ${B}">${escapeHtml(t(D))}</span>
                    <div class="notif-rule-main">
                        <div class="notif-rule-name">${escapeHtml(L.name)}</div>
                        <div class="notif-rule-meta">${Y}</div>
                    </div>
                    <div class="notif-rule-actions">
                        <button class="notif-rule-toggle ${L.enabled?"on":""}" data-action="toggle" aria-label="toggle"></button>
                        <button class="notif-rule-btn" data-action="test">${escapeHtml(t("notif-action-test"))}</button>
                        <button class="notif-rule-btn danger" data-action="delete">${escapeHtml(t("notif-action-delete"))}</button>
                    </div>
                </div>`}).join("")}}function d(j){const _=e("notif-logs-list");if(_){if(!j.length){_.innerHTML='<div class="notif-logs-empty">'+escapeHtml(t("notif-logs-empty"))+"</div>";return}_.innerHTML=j.map(h=>{const w=h.status==="sent",L=h.event_type==="exception_high"?"notif-event-exception-high":h.event_type==="large_invoice"?"notif-event-large-invoice":"notif-event-test-send",S=w?"":" · "+escapeHtml(h.error||"failed");return`
                <div class="notif-log-row">
                    <span class="notif-log-status ${w?"":"failed"}"></span>
                    <div class="notif-log-main">
                        <div class="notif-log-event">${escapeHtml(t(L))}</div>
                        <div class="notif-log-meta">${escapeHtml(h.template_code||"-")}${S}</div>
                    </div>
                    <div class="notif-log-time">${u(h.sent_at)}</div>
                </div>`}).join("")}}async function c(){try{const j=await apiGet("/api/notifications/rules");p=j&&j.items||[],l(p)}catch(j){console.warn("load rules fail",j)}try{const j=await apiGet("/api/notifications/logs?limit=20");f=j&&j.items||[],d(f)}catch(j){console.warn("load logs fail",j)}}let p=null,f=null;function m(){p&&l(p),f&&d(f);const j=e("notif-new-modal");j&&j.style.display!=="none"&&o&&i(e("notif-line-check"),!!(o&&o.bound))}function b(){const j=e("notif-new-modal");j&&(j.style.display="",e("notif-new-name").value="",e("notif-new-threshold").value="",e("notif-new-threshold-row").style.display="none",document.querySelectorAll('input[name="notif-template"]').forEach(_=>_.checked=!1),s().then(_=>i(e("notif-line-check"),!!(_&&_.bound))))}function M(){const j=e("notif-new-modal");j&&(j.style.display="none")}function I(){const j=document.querySelector('input[name="notif-template"]:checked'),_=e("notif-new-threshold-row");if(!j){_.style.display="none";return}_.style.display=j.value==="large_invoice"?"":"none";const h=e("notif-new-name");h&&!h.value.trim()&&(h.value=j.value==="large_invoice"?t("notif-tmpl-large-name"):t("notif-tmpl-exception-name"))}async function x(){const j=document.querySelector('input[name="notif-template"]:checked');if(!j){showToast(t("notif-new-template"),"error");return}const _=(e("notif-new-name").value||"").trim();if(!_){showToast(t("notif-name-required"),"error");return}const h={name:_,template_code:j.value,params:{},enabled:!0};if(j.value==="large_invoice"){const w=parseFloat(e("notif-new-threshold").value||"0");if(!w||w<=0){showToast(t("notif-threshold-required"),"error");return}h.params.threshold=w}try{const w=await apiPost("/api/notifications/rules",h);if(w&&w.ok)showToast(t("notif-toast-created"),"success"),M(),c();else{const L=await(w&&w.json&&w.json().catch(()=>({})))||{};showToast(L&&L.detail||"save failed","error")}}catch{showToast("save failed","error")}}async function y(j,_,h){if(j==="toggle"){const w=h.classList.contains("on"),L=await n("/api/notifications/rules/"+_,{enabled:!w});L&&L.ok?(showToast(t(w?"notif-toast-toggled-off":"notif-toast-toggled-on"),"success"),c()):showToast("toggle failed","error");return}if(j==="test"){const w=await s();if(!w||!w.bound){showToast(t("notif-line-error-bind-first"),"error");return}const L=await apiPost("/api/notifications/rules/"+_+"/test",{});if(L&&L.ok)showToast(t("notif-toast-test-sent"),"success"),c();else{const S=await(L&&L.json&&L.json().catch(()=>({})))||{},D=S&&S.detail||"";showToast(D||t("notif-toast-test-failed"),"error"),c()}return}if(j==="delete"){if(!await showConfirm(t("notif-confirm-delete"),{danger:!0}))return;const L=await a("/api/notifications/rules/"+_);L&&L.ok?(showToast(t("notif-toast-deleted"),"success"),c()):showToast("delete failed","error");return}}let $=!1;function C(){if($)return;$=!0;const j=e("notif-btn-new");j&&j.addEventListener("click",b);const _=e("notif-btn-refresh-logs");_&&_.addEventListener("click",c);const h=e("notif-new-close");h&&h.addEventListener("click",M);const w=e("notif-new-cancel");w&&w.addEventListener("click",M);const L=e("notif-new-save");L&&L.addEventListener("click",x),document.querySelectorAll('input[name="notif-template"]').forEach(B=>{B.addEventListener("change",I)});const S=e("notif-rules-list");S&&S.addEventListener("click",B=>{const P=B.target.closest("button[data-action]");if(!P)return;const Y=P.closest("[data-rule-id]");Y&&y(P.getAttribute("data-action"),Y.getAttribute("data-rule-id"),P)});const D=e("notif-new-modal");D&&D.addEventListener("click",B=>{B.target===D&&M()})}async function F(){C(),await c()}window._loadNotificationsPanel=F,window._rerenderNotifications=m})();(function(){function n(x,y){try{return window.t&&window.t(x)||y}catch{return y}}function a(){var x="";try{x=localStorage.getItem("mrpilot_token")||""}catch{}return x?{Authorization:"Bearer "+x}:{}}var o=[{tbody:"vex-task-tbody",api:"/api/recon/tasks/batch_delete",reload:function(){try{window.loadRecentTasks&&window.loadRecentTasks()}catch{}},kind:"vex"},{tbody:"glv-history-tbody",api:"/api/recon/gl-vat/tasks/batch_delete",reload:function(){try{window._loadGlvHistory&&window._loadGlvHistory()}catch{}},kind:"glv"},{tbody:"brv2-history-tbody",api:"/api/recon/bank-v2/tasks/batch_delete",reload:function(){try{window._brv2LoadHistory&&window._brv2LoadHistory()}catch{}},kind:"brv2"}];function s(){if(!document.getElementById("recon-batch-style")){var x=document.createElement("style");x.id="recon-batch-style",x.textContent=".recon-sel-cell{width:36px;text-align:center;padding-left:10px!important;padding-right:6px!important}.recon-sel-cb,.recon-master-cb{cursor:pointer;width:14px;height:14px;accent-color:#111;margin:0;vertical-align:middle}th.recon-time-col,td.recon-time-col{white-space:nowrap}tr.recon-thead-batch{display:none}thead.recon-batch-mode tr.recon-thead-default{display:none}thead.recon-batch-mode tr.recon-thead-batch{display:table-row}tr.recon-thead-batch th{background:#fafaf8;border-bottom:1px solid #e8e8e3;padding:8px 12px}tr.recon-thead-batch .recon-batch-inline{display:flex;align-items:center;gap:10px;font-size:12px;color:#111;font-weight:normal}tr.recon-thead-batch .recon-batch-count-inline{font-weight:600;color:#111;margin-right:4px}tr.recon-thead-batch .recon-batch-del-inline{background:#dc2626;color:#fff;border:none;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:4px}tr.recon-thead-batch .recon-batch-del-inline:hover{background:#b91c1c}tr.recon-thead-batch .recon-batch-clear-inline{background:transparent;border:none;color:#555;cursor:pointer;font-size:12px;font-family:inherit;text-decoration:underline;padding:4px 2px}tr.recon-thead-batch .recon-batch-clear-inline:hover{color:#111}.recon-batch-bar{display:none!important}",document.head.appendChild(x)}}function i(x){return x?x.dataset&&x.dataset.taskId?x.dataset.taskId:x.dataset&&x.dataset.taskid?x.dataset.taskid:"":""}function r(x){var y=document.getElementById(x.tbody);if(!y)return null;var $=y.closest("table");if(!$)return null;var C=$.querySelector("thead");if(!C)return null;if(C._reconReady)return C;var F=C.querySelector("tr");if(!F)return null;if(F.classList.add("recon-thead-default"),!F.querySelector(".recon-master-cb")){var j=document.createElement("th");j.className="recon-sel-cell";var _=document.createElement("input");_.type="checkbox",_.className="recon-master-cb",_.setAttribute("aria-label","select all"),_.addEventListener("change",function(){c(x,_.checked)}),j.appendChild(_),F.insertBefore(j,F.firstElementChild)}var h=F.children[1];h&&!h.classList.contains("recon-time-col")&&h.classList.add("recon-time-col");var w=F.children.length,L=document.createElement("tr");L.className="recon-thead-batch";var S=document.createElement("th");S.className="recon-sel-cell";var D=document.createElement("input");D.type="checkbox",D.className="recon-master-cb",D.checked=!0,D.setAttribute("aria-label","select all"),D.addEventListener("change",function(){c(x,D.checked)}),S.appendChild(D);var B=document.createElement("th");return B.setAttribute("colspan",String(w-1)),B.innerHTML='<div class="recon-batch-inline"><span class="recon-batch-count-inline" data-recon-count></span><button type="button" class="recon-batch-del-inline" data-recon-del><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg><span data-recon-del-label></span></button><button type="button" class="recon-batch-clear-inline" data-recon-clear></button></div>',L.appendChild(S),L.appendChild(B),C.appendChild(L),B.querySelector("[data-recon-del]").addEventListener("click",function(){b(x)}),B.querySelector("[data-recon-clear]").addEventListener("click",function(){m(x)}),C._reconReady=!0,f(x),C}function u(x){var y=document.getElementById(x.tbody);if(y){var $=y.querySelectorAll("tr");$.forEach(function(C){var F=i(C);if(F&&!C.querySelector(".recon-sel-cb")){var j=C.querySelector("td");if(j){var _=document.createElement("td");_.className="recon-sel-cell";var h=document.createElement("input");h.type="checkbox",h.className="recon-sel-cb",h.dataset.taskId=F,h.dataset.kind=x.kind,h.addEventListener("click",function(L){L.stopPropagation()}),h.addEventListener("change",function(){p(x)}),_.appendChild(h),C.insertBefore(_,j);var w=C.children[1];w&&!w.classList.contains("recon-time-col")&&w.classList.add("recon-time-col")}}}),p(x)}}function l(x){var y=document.getElementById(x.tbody);return y?Array.prototype.slice.call(y.querySelectorAll(".recon-sel-cb")):[]}function d(x){return l(x).filter(function(y){return y.checked}).map(function(y){return y.dataset.taskId})}function c(x,y){l(x).forEach(function($){$.checked=!!y}),p(x)}function p(x){var y=d(x),$=l(x),C=document.getElementById(x.tbody);if(C){var F=C.closest("table"),j=F&&F.querySelector("thead");if(j){y.length>0?j.classList.add("recon-batch-mode"):j.classList.remove("recon-batch-mode"),j.querySelectorAll(".recon-master-cb").forEach(function(h){if($.length===0){h.checked=!1,h.indeterminate=!1;return}y.length===$.length?(h.checked=!0,h.indeterminate=!1):y.length===0?(h.checked=!1,h.indeterminate=!1):(h.checked=!1,h.indeterminate=!0)});var _=j.querySelector("[data-recon-count]");_&&(_.textContent=n("recon-batch-selected-n","已选 {n} 条").replace("{n}",y.length))}}}function f(x){var y=document.getElementById(x.tbody);if(y){var $=y.closest("table"),C=$&&$.querySelector("thead");if(C){var F=C.querySelector("[data-recon-del-label]"),j=C.querySelector("[data-recon-clear]");F&&(F.textContent=n("recon-batch-delete","批量删除")),j&&(j.textContent=n("recon-batch-clear","取消")),p(x)}}}function m(x){l(x).forEach(function(y){y.checked=!1}),p(x)}async function b(x){var y=d(x);if(y.length){var $=n("recon-batch-delete-confirm","确定删除选中的 {n} 条对账任务?此操作不可恢复").replace("{n}",y.length),C=!1;try{typeof window.pearnlyConfirm=="function"?C=await window.pearnlyConfirm($,n("recon-batch-delete-title","批量删除")):C=window.confirm($)}catch{C=!1}if(C)try{var F=Object.assign({"Content-Type":"application/json"},a()),j=x.kind==="glv"?y.map(function(L){return parseInt(L,10)}):y,_=await fetch(x.api,{method:"POST",headers:F,body:JSON.stringify({ids:j})});if(!_.ok){typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error");return}var h=await _.json(),w=h&&(h.deleted!=null?h.deleted:h.count)||y.length;typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-ok","已删除 {n} 条").replace("{n}",w),"success"),x.reload()}catch{typeof window.showToast=="function"&&window.showToast(n("recon-batch-delete-fail","批量删除失败"),"error")}}}function M(x){r(x),u(x);var y=document.getElementById(x.tbody);if(!(!y||y._reconBatchWatched)){y._reconBatchWatched=!0;var $=new MutationObserver(function(){u(x)});$.observe(y,{childList:!0,subtree:!1})}}function I(){s(),o.forEach(M),document.querySelectorAll(".recon-batch-bar").forEach(function(x){try{x.remove()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",I):I(),setTimeout(I,1500),setTimeout(I,4e3),document.addEventListener("keydown",function(x){x.key==="Escape"&&o.forEach(function(y){d(y).length>0&&m(y)})}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-batch-thead",function(){o.forEach(f)})})();(function(){let e={role:"",monthly_volume:"",country:"",line_id:""},n=1;const a=4,o="pilot_ob_dismiss",s="pilot_ob_done";window.maybeShowOnboarding=function(d){};function i(d){n=d;for(let f=1;f<=a;f++){const m=document.getElementById("ob-step-"+f);m&&(m.style.display=f===d?"block":"none")}document.querySelectorAll(".ob-dot").forEach(f=>{const m=parseInt(f.dataset.step,10);f.classList.toggle("active",m===d),f.classList.toggle("done",m<d)});const c=document.getElementById("ob-step-label");c&&(c.textContent=d+" / "+a);const p=document.getElementById("ob-next");if(p&&(p.textContent=d===a?t("ob-finish"):t("ob-next")),d===4){const f=document.getElementById("ob-line-input");f&&(f.value=e.line_id||"")}}function r(d){const c=document.querySelector(".onboarding-modal");if(!c)return;let p=c.querySelector(".ob-feedback");p||(p=document.createElement("div"),p.className="ob-feedback",c.appendChild(p)),p.textContent=d,p.classList.add("show"),setTimeout(()=>p.classList.remove("show"),1800)}document.addEventListener("click",d=>{const c=d.target.closest(".ob-option");if(!c)return;const p=c.parentElement;if(!p||!p.classList.contains("ob-options"))return;p.querySelectorAll(".ob-option").forEach(m=>m.classList.remove("selected")),c.classList.add("selected");const f=c.dataset.value;p.id==="ob-role-options"?e.role=f:p.id==="ob-volume-options"?e.monthly_volume=f:p.id==="ob-country-options"&&(e.country=f)}),document.addEventListener("click",d=>{d.target.id==="ob-skip"&&u()}),document.addEventListener("click",d=>{if(d.target.id==="ob-next"){if(n===4){const c=document.getElementById("ob-line-input");e.line_id=(c&&c.value||"").trim().replace(/^@+/,"")}u()}}),document.addEventListener("click",d=>{if(d.target.closest("#ob-close")){localStorage.setItem(o,String(Date.now()));const c=document.getElementById("onboarding-modal");c&&(c.style.display="none")}});function u(){n===1&&e.role?r(t("ob-fb-role")):n===2&&e.monthly_volume?r(t("ob-fb-volume")):n===3&&e.country?r(t("ob-fb-country")):n===4&&e.line_id&&r(t("ob-fb-line")),n<a?setTimeout(()=>i(n+1),e[Object.keys(e)[n-1]]?350:0):l()}async function l(){const d=document.getElementById("onboarding-modal");localStorage.setItem(s,"1"),localStorage.removeItem(o);const c={};if(e.role&&(c.role=e.role),e.monthly_volume&&(c.monthly_volume=e.monthly_volume),e.country&&(c.country=e.country),e.line_id&&(c.line_id=e.line_id),Object.keys(c).length===0){d&&(d.style.display="none");return}try{const p=await fetch("/api/me/profile",{method:"PUT",headers:{Authorization:"Bearer "+(window.token||localStorage.getItem("mrpilot_token")),"Content-Type":"application/json"},body:JSON.stringify(c)});p.ok?(r(t("ob-fb-done")),window._userInfo&&Object.assign(window._userInfo,c),setTimeout(()=>{d&&(d.style.display="none")},1200)):(localStorage.setItem("pilot_ob_pending",JSON.stringify(c)),console.warn("onboarding profile save failed",p.status),r(t("ob-fb-saved-local")),setTimeout(()=>{d&&(d.style.display="none")},1500))}catch(p){console.error("onboarding submit",p),localStorage.setItem("pilot_ob_pending",JSON.stringify(c)),d&&(d.style.display="none")}}})();(function(){const e=document.getElementById("archive-rule-modal");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
        </div>`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])})}catch{}}})();(function(){let e=[],n="by_month_seller",a=-1,o=!1;const s={date:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.5"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>',seller:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13.5V4a1 1 0 011-1h5a1 1 0 011 1v9.5"/><path d="M10 7h2.5a.5.5 0 01.5.5v6"/><path d="M5 6h1M5 9h1M5 12h1M13.5 13.5h-12"/></svg>',category:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 2h6L13 5.5v7.5a1 1 0 01-1 1H3.5a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M9 2v4h4"/><path d="M5 9h6M5 11.5h4"/></svg>',amount:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M8 4.5v7M10 6.3a1.8 1.8 0 00-4 0c0 .9.7 1.3 2 1.6s2 .8 2 1.6a1.8 1.8 0 01-4 0"/></svg>',invoice:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3.5l1.5 10.5 1.5-1 1.5 1 1.5-1 1.5 1 1.5-1 1.5 1L13 3.5z"/><path d="M5.5 6.5h5M5.5 9h5M5.5 11.5h3"/></svg>',buyer:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2.5"/><path d="M3 13.5c0-2.5 2.2-4.5 5-4.5s5 2 5 4.5"/></svg>',sep:'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v10"/></svg>'},i={date:{label:"field-date",defaultCfg:{format:"YYYY-MM-DD"}},seller:{label:"field-seller",defaultCfg:{short:!0}},category:{label:"field-category",defaultCfg:{}},amount:{label:"field-amount",defaultCfg:{with_currency:!0}},invoice:{label:"field-invoice",defaultCfg:{}},buyer:{label:"field-buyer",defaultCfg:{}},sep:{label:"field-sep",defaultCfg:{val:"_"}}};function r(){return{zh:"运费",en:"Shipping",th:"ค่าขนส่ง",ja:"送料"}[currentLang]||"Shipping"}function u(){return"DHL Express (Thailand) Co., Ltd."}function l(){return{merged_fields:{invoice_date:"2026-04-15",seller_name:u(),category:r(),total_amount:1250,currency:"THB",invoice_no:"INV-2026030002",buyer_name:"Mr.ERP Co., Ltd."}}}window.loadAboutPanel=()=>d(),window.loadPrefsSettings=()=>c(),window.loadArchiveSettings=()=>f();function d(){const _=document.getElementById("settings-contact-grid");if(!_)return;const h=_contact?.phone||"086-889-2228",w=_contact?.line_id||"@Pearnly",L=_contact?.line_url||"https://line.me/R/ti/p/@059oupmg",S=_contact?.email||"hello@pearnly.com",D=_contact?.address||"Bangkok, Thailand";_.innerHTML=`
            <a class="contact-item" href="${escapeHtml(L)}" target="_blank" rel="noopener">
                <div class="contact-icon line">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.282.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-line"))}</div>
                    <div class="contact-value">${escapeHtml(w)}</div>
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
            <a class="contact-item" href="tel:${escapeHtml(h.replace(/[^\d+]/g,""))}">
                <div class="contact-icon phone">
                    <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 3a1 1 0 011-1h2.5a1 1 0 01.97.757l1 4a1 1 0 01-.29.986l-1.75 1.75a11 11 0 005.07 5.07l1.75-1.75a1 1 0 01.986-.29l4 1a1 1 0 01.757.97V17a1 1 0 01-1 1h-1C8.82 18 2 11.18 2 3V3z"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-phone"))}</div>
                    <div class="contact-value">${escapeHtml(h)}</div>
                </div>
            </a>
            <div class="contact-item">
                <div class="contact-icon address">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s-7-7.5-7-13a7 7 0 1114 0c0 5.5-7 13-7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>
                </div>
                <div class="contact-text">
                    <div class="contact-label">${escapeHtml(t("contact-address"))}</div>
                    <div class="contact-value">${escapeHtml(D)}</div>
                </div>
            </div>
        `}async function c(){try{const _=await fetch("/api/settings/dup-check",{headers:{Authorization:"Bearer "+token}});if(!_.ok)return;const h=await _.json(),w=document.getElementById("pref-dup-check");w&&(w.checked=!!h.enabled)}catch(_){console.warn("load prefs failed",_)}}const p=document.getElementById("pref-dup-check");p&&!p.dataset.bound&&(p.dataset.bound="1",p.addEventListener("change",async _=>{const h=_.target.checked;try{(await fetch("/api/settings/dup-check",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({enabled:h})})).ok?showToast(h?t("pref-dup-check-on-toast"):t("pref-dup-check-off-toast"),"success"):(_.target.checked=!h,showToast(t("pref-save-failed"),"error"))}catch{_.target.checked=!h,showToast(t("pref-save-failed"),"error")}}));async function f(){const _=!!(_userInfo&&_userInfo.can_customize_archive);o=!_;const h=document.getElementById("archive-upgrade-banner");h&&(h.style.display=_?"none":"");const w=document.getElementById("archive-plus-badge");w&&(w.style.display=_?"none":"");try{const L=await fetch("/api/archive/settings",{headers:{Authorization:"Bearer "+token}});if(!L.ok)throw new Error("load failed");const S=await L.json();e=Array.isArray(S.name_template)?S.name_template:[],n=S.folder_strategy||"by_month_seller"}catch(L){console.error("load archive settings failed",L),showToast(t("archive-load-failed"),"error");return}m(),b(),M(),I()}function m(){const _=document.getElementById("archive-rule-canvas");if(_){if(e.length===0){_.innerHTML=`<div class="archive-empty">${escapeHtml(t("archive-rule-empty"))}</div>`;return}_.innerHTML=e.map((h,w)=>{const L=i[h.type]||{label:h.type},S=s[h.type]||"",D=h.type==="sep"?`"${escapeHtml(h.val||"_")}"`:escapeHtml(t(L.label));return`
                <span class="archive-token ${h.type}"
                      data-token-idx="${w}"
                      draggable="${o?"false":"true"}">
                    <span class="token-icon">${S}</span>
                    <span class="token-label">${D}</span>
                </span>
            `}).join("")}}function b(){const _=document.getElementById("archive-field-palette");if(!_)return;const h=["date","seller","category","amount","invoice","buyer","sep"];_.innerHTML=h.map(w=>{const L=i[w],S=s[w]||"";return`
                <button class="archive-palette-btn ${w}" data-add-field="${w}" ${o?"disabled":""}>
                    <span class="token-icon">${S}</span>
                    <span>${escapeHtml(t(L.label))}</span>
                </button>
            `}).join("")}function M(){document.querySelectorAll('input[name="folder-strategy"]').forEach(_=>{_.checked=_.value===n,_.disabled=o})}async function I(){const _=document.getElementById("archive-preview-name"),h=document.getElementById("archive-preview-hint");if(h&&(h.textContent=t("archive-preview-hint",{category:r()})),!!_){if(e.length===0){_.textContent="-";return}try{const L=await(await fetch("/api/archive/rename-preview",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({merged_fields:l().merged_fields,name_template:e})})).json();_.textContent=(L.name||"-")+".pdf"}catch{_.textContent="("+t("archive-preview-error")+")"}}}window._rerenderArchiveAll=function(){const _=document.getElementById("archive-rule-modal");!_||_.style.display==="none"||(m(),b(),I())};let x=-1;document.addEventListener("dragstart",_=>{const h=_.target.closest(".archive-token");!h||o||(x=parseInt(h.dataset.tokenIdx,10),h.classList.add("dragging"),_.dataTransfer.effectAllowed="move")}),document.addEventListener("dragend",_=>{document.querySelectorAll(".archive-token").forEach(h=>h.classList.remove("dragging","drop-target")),x=-1}),document.addEventListener("dragover",_=>{const h=_.target.closest(".archive-token");h&&(_.preventDefault(),_.dataTransfer.dropEffect="move",document.querySelectorAll(".archive-token").forEach(w=>w.classList.remove("drop-target")),h.classList.add("drop-target"))}),document.addEventListener("drop",_=>{const h=_.target.closest(".archive-token");if(!h||x<0||o)return;_.preventDefault();const w=parseInt(h.dataset.tokenIdx,10);if(w===x)return;const L=e.splice(x,1)[0];e.splice(w,0,L),x=-1,m(),I()}),document.addEventListener("click",_=>{if(_.target.closest("#btn-open-archive-rule")||_.target.closest("#btn-open-archive-rule-from-settings")){const S=document.getElementById("archive-rule-modal");S&&(S.style.display="",f());return}if(_.target.closest("#archive-rule-modal-close")||_.target.id==="archive-rule-modal"){const S=document.getElementById("archive-rule-modal");S&&(S.style.display="none");return}const h=_.target.closest(".settings-nav-item");if(h){switchSettingsTab(h.dataset.settingsTab);return}if(o&&_.target.closest(".archive-token, [data-add-field], #btn-archive-save, #btn-archive-reset")){showToast(t("feature-contact-us"),"info");return}const w=_.target.closest("[data-add-field]");if(w){const S=w.dataset.addField,D=i[S],B={type:S,...D.defaultCfg};e.push(B),m(),I();return}const L=_.target.closest(".archive-token");if(L&&!o){y(parseInt(L.dataset.tokenIdx,10));return}if(_.target.closest("#btn-archive-save"))return F();if(_.target.closest("#btn-archive-reset"))return j();(_.target.closest("#archive-token-close")||_.target.id==="archive-token-modal")&&(document.getElementById("archive-token-modal").style.display="none"),_.target.closest("#btn-archive-token-ok")&&$(),_.target.closest("#btn-archive-token-delete")&&C()}),document.addEventListener("change",_=>{_.target.name==="folder-strategy"&&(n=_.target.value)});function y(_){a=_;const h=e[_];if(!h)return;const w=document.getElementById("archive-token-body");let L="";h.type==="date"?L=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-date-format"))}</label>
                    <select class="form-input" id="token-date-format">
                        <option value="YYYY-MM-DD" ${h.format==="YYYY-MM-DD"?"selected":""}>YYYY-MM-DD (2026-04-15)</option>
                        <option value="YYYYMMDD"   ${h.format==="YYYYMMDD"?"selected":""}>YYYYMMDD (20260415)</option>
                        <option value="YY.MM"      ${h.format==="YY.MM"?"selected":""}>YY.MM (26.04)</option>
                        <option value="YYYY年MM月" ${h.format==="YYYY年MM月"?"selected":""}>YYYY年MM月 (2026年04月)</option>
                    </select>
                </div>`:h.type==="seller"?L=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-seller-short" ${h.short?"checked":""}> ${escapeHtml(t("archive-seller-short"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-seller-short-hint"))}</div>
                </div>`:h.type==="amount"?L=`
                <div class="form-group">
                    <label class="form-label"><input type="checkbox" id="token-amount-currency" ${h.with_currency?"checked":""}> ${escapeHtml(t("archive-amount-currency"))}</label>
                    <div class="form-hint">${escapeHtml(t("archive-amount-currency-hint"))}</div>
                </div>`:h.type==="sep"?L=`
                <div class="form-group">
                    <label class="form-label">${escapeHtml(t("archive-sep-val"))}</label>
                    <div class="sep-options">
                        <button type="button" class="sep-chip ${h.val==="_"?"active":""}" data-sep="_">_ (下划线)</button>
                        <button type="button" class="sep-chip ${h.val==="-"?"active":""}" data-sep="-">- (短横)</button>
                        <button type="button" class="sep-chip ${h.val===" "?"active":""}" data-sep=" ">(空格)</button>
                        <input type="text" id="token-sep-custom" class="form-input sep-custom" maxlength="3" placeholder="${escapeHtml(t("archive-sep-custom"))}" value="${["_","-"," "].includes(h.val)?"":escapeHtml(h.val||"")}">
                    </div>
                </div>`:L=`<div class="form-hint">${escapeHtml(t("archive-token-no-option"))}</div>`,w.innerHTML=L,document.getElementById("archive-token-modal").style.display="",w.querySelectorAll(".sep-chip").forEach(S=>{S.addEventListener("click",()=>{w.querySelectorAll(".sep-chip").forEach(B=>B.classList.remove("active")),S.classList.add("active");const D=document.getElementById("token-sep-custom");D&&(D.value="")})})}function $(){const _=e[a];if(_){if(_.type==="date")_.format=document.getElementById("token-date-format").value;else if(_.type==="seller")_.short=document.getElementById("token-seller-short").checked;else if(_.type==="amount")_.with_currency=document.getElementById("token-amount-currency").checked;else if(_.type==="sep"){const h=document.querySelector("#archive-token-body .sep-chip.active"),w=document.getElementById("token-sep-custom").value;_.val=w||(h?h.dataset.sep:"_")}document.getElementById("archive-token-modal").style.display="none",m(),I()}}function C(){a<0||(e.splice(a,1),document.getElementById("archive-token-modal").style.display="none",m(),I())}async function F(){if(e.length===0){showToast(t("archive-rule-cannot-empty"),"error");return}try{if(!(await fetch("/api/archive/settings",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({name_template:e,folder_strategy:n})})).ok)throw new Error("save failed");showToast(t("archive-save-ok"),"success");const h=document.getElementById("archive-rule-modal");h&&(h.style.display="none")}catch{showToast(t("archive-save-fail"),"error")}}async function j(){await showConfirm(t("archive-reset-confirm"),{danger:!0})&&(e=[{type:"date",format:"YYYY-MM-DD"},{type:"sep",val:"_"},{type:"seller",short:!0},{type:"sep",val:"_"},{type:"category"},{type:"sep",val:"_"},{type:"amount",with_currency:!0}],n="by_month_seller",m(),M(),I())}})();(function(){const o="pearnly_big_batch_tip_shown";let s=null,i=null,r=0,u=0,l=!1;function d(y){const $=typeof t=="function"?t("big-batch-unload-warn"):"Batch OCR running · close anyway?";return y.preventDefault(),y.returnValue=$,$}function c(){l||(l=!0,window.addEventListener("beforeunload",d))}function p(){l&&(l=!1,window.removeEventListener("beforeunload",d))}function f(){if(document.getElementById("big-batch-progress"))return;const y=document.getElementById("file-list");if(!y||!y.parentNode)return;const $=document.createElement("div");$.id="big-batch-progress",$.className="big-batch-progress",$.innerHTML='<div class="bbp-row"><svg class="bbp-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 4.5v3.5l2.5 1.5"/></svg><span class="bbp-text" id="bbp-text"></span></div><div class="bbp-track"><div class="bbp-fill" id="bbp-fill" style="width:0%"></div></div>',y.parentNode.insertBefore($,y);const C=document.getElementById("bbp-text");C&&(C.textContent=typeof t=="function"?t("big-batch-progress-init"):"Starting...")}function m(){const y=document.getElementById("big-batch-progress");y&&y.remove()}function b(){if(!i)return;let y=0;for(let L=0;L<i.length;L++){const S=i[L].status;(S==="success"||S==="error"||S==="cancelled")&&y++}const $=r,C=$>0?Math.min(100,Math.floor(100*y/$)):0,F=(Date.now()-u)/1e3;let j;if(y>=3&&F>1){const L=F/y;j=($-y)*L}else j=($-y)*6/6;const _=Math.max(1,Math.ceil(j/60)),h=document.getElementById("bbp-fill"),w=document.getElementById("bbp-text");h&&(h.style.width=C+"%"),w&&(y>=$?w.textContent=t("big-batch-progress-done").replace("{total}",$):w.textContent=t("big-batch-progress-running").replace("{done}",y).replace("{total}",$).replace("{min}",_))}function M(y){try{if(localStorage.getItem(o)==="1")return}catch{}const $=Math.max(1,Math.ceil(y*6/6/60)),C=t("big-batch-first-tip").replace("{n}",y).replace("{min}",$);typeof showToast=="function"&&showToast(C,"info",8e3);try{localStorage.setItem(o,"1")}catch{}}function I(y){!y||y.length<100||(i=y,r=y.length,u=Date.now(),f(),c(),M(r),s&&clearInterval(s),s=setInterval(b,250),b())}function x(){s&&(clearInterval(s),s=null),p(),i&&r>=100?(b(),setTimeout(m,1200)):m(),i=null,r=0}window._bigBatchStart=I,window._bigBatchStop=x,typeof window.subscribeI18n=="function"&&window.subscribeI18n("big-batch-progress",function(){i&&b()})})();(function(){let e=null,n=!1,a=!1;function o(h){return typeof escapeHtml=="function"?escapeHtml(h==null?"":String(h)):String(h??"")}function s(h,w){try{typeof showToast=="function"&&showToast(h,w||"info")}catch{}}function i(){const h=typeof _userInfo<"u"?_userInfo:null;return!!(h&&(h.role==="owner"||h.is_super_admin))}function r(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function u(h){if(!h)return!1;const w=String(h.status||"").toLowerCase();return w==="exception"||w==="exception_pending"||w==="rejected"}async function l(h){if(n&&!h)return e;const w=localStorage.getItem("mrpilot_token");if(!w)return null;try{const L=await fetch("/api/erp/xero/status",{headers:{Authorization:"Bearer "+w}});if(!L.ok)throw new Error("http_"+L.status);e=await L.json(),n=!0}catch{e={configured:!1,connected:!1,organisations:[]},n=!1}return e}function d(){const h=document.getElementById("erp-connect-cards");if(!h)return;const w=e;let L,S=!1;w?w.configured?w.connected?(S=!0,L='<span class="mrerp-card-pill mrerp-pill-ok">'+o(t("xero-card-connected"))+"</span>"):L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-configured"))+"</span>":L='<span class="mrerp-card-pill mrerp-pill-neutral">'+o(t("xero-card-not-connected"))+"</span>";let D="";if(!w||!w.configured)D='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>";else if(!w.connected)i()&&(D='<button type="button" class="int-btn-configure" id="btn-xero-connect">'+o(t("xero-connect-btn"))+"</button>");else{const E=!!w.auto_push,g=E?t("card-btn-disable"):t("card-btn-enable");D='<button type="button" class="'+(E?"mrerp-card-toggle mrerp-card-toggle-disable":"mrerp-card-toggle mrerp-card-toggle-enable")+'" id="btn-xero-toggle-enabled" data-xero-enabled="'+(E?"1":"0")+'" title="'+o(E?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip"))+'">'+o(g)+'</button><button type="button" class="int-btn-configure" id="btn-xero-edit-toggle">'+o(t("card-btn-edit"))+"</button>"}const B=w&&w.connected?"xero-card-desc-connected":"xero-card-desc-default",P=w&&w.connected?t("xero-card-connected")||"Connected · default org will receive pushes":"Cloud accounting · push invoices to your default Xero org",Y=(function(){const E=t(B);return E===B?P:E})();let G='<div class="integration-row erp-connect-xero'+(S?" connected":"")+'"><div class="int-icon ic-xero"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1.3" fill="currentColor"/><circle cx="15" cy="14" r="1.3" fill="currentColor"/><path d="M9 14l6-4"/></svg></div><div class="int-info"><div class="int-name"><span>'+o(t("xero-card-title")||"Xero")+"</span>"+L+'</div><div class="int-desc">'+o(Y)+'</div></div><div class="int-actions">'+D+"</div></div>";if(w&&w.configured&&w.connected&&i()){const E=w.organisations||[];let g="";if(E.length>0){g+='<div class="erp-cc-meta">'+o((t("xero-org-count")||"").replace("{n}",String(E.length)))+"</div>",g+='<div class="erp-cc-org-label">'+o(t("xero-default-org"))+":</div>",g+='<div class="erp-cc-orgs">',E.forEach(function(K){g+='<label class="erp-cc-org-row"><input type="radio" name="xero-default-org" value="'+o(K.id)+'"'+(K.is_default?" checked":"")+'><span class="erp-cc-org-name">'+o(K.organisation_name||K.organisation_id)+"</span></label>"}),g+="</div>";const q=!!w.auto_push,N=q?t("erp-auto-push-on-tip"):t("erp-auto-push-off-tip");g+='<div class="erp-cc-auto-push" title="'+o(N)+'"><label class="erp-cc-toggle"><input type="checkbox" id="xero-auto-push-toggle"'+(q?" checked":"")+'><span class="erp-cc-toggle-slider"></span><span class="erp-cc-toggle-label">'+o(t("erp-auto-push-label"))+"</span></label></div>",g+='<div class="erp-cc-actions"><button class="btn btn-ghost btn-tiny" type="button" id="btn-xero-disconnect">'+o(t("xero-disconnect-btn"))+"</button></div>"}G+='<div class="erp-xero-details" id="erp-xero-details" style="display:none; margin:8px 0 16px; padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:var(--bg);">'+g+"</div>"}const W=h.querySelector(".erp-connect-xero"),te=h.querySelector("#erp-xero-details");te&&te.remove(),W?W.outerHTML=G:h.insertAdjacentHTML("afterbegin",G);const re=document.getElementById("btn-xero-edit-toggle");re&&re.addEventListener("click",function(E){E.preventDefault();const g=document.getElementById("erp-xero-details");g&&(g.style.display=g.style.display==="none"?"":"none")});const H=document.getElementById("btn-xero-toggle-enabled");H&&H.addEventListener("click",async function(E){if(E.preventDefault(),H.disabled)return;const q=!(H.getAttribute("data-xero-enabled")==="1");if(!q)try{if(!await window.pearnlyConfirm(t("card-toggle-disable-confirm")))return}catch{}H.disabled=!0,await m(q,null)})}async function c(){const h=localStorage.getItem("mrpilot_token");if(h)try{const w=await fetch("/api/erp/xero/auth/start",{method:"GET",headers:{Authorization:"Bearer "+h}});if(!w.ok){let S="unknown";try{S=(await w.json()).detail||"unknown"}catch{}const D=String(S).replace(/^xero\./,"").toLowerCase();s(t("xero-push-fail").replace("{err}",t("xero-err-"+D)||S),"error");return}const L=await w.json();L.redirect_url&&(window.location.href=L.redirect_url)}catch(w){s(t("xero-push-fail").replace("{err}",w.message||"network"),"error")}}async function p(){if(!await window.pearnlyConfirm(t("xero-disconnect-confirm")))return;const w=localStorage.getItem("mrpilot_token");try{const L=await fetch("/api/erp/xero/disconnect",{method:"POST",headers:{Authorization:"Bearer "+w}});if(!L.ok)throw new Error("http_"+L.status);await l(!0),d()}catch(L){s(t("xero-push-fail").replace("{err}",L.message),"error")}}async function f(h){const w=localStorage.getItem("mrpilot_token");try{const L=await fetch("/api/erp/xero/select_org",{method:"POST",headers:{Authorization:"Bearer "+w,"Content-Type":"application/json"},body:JSON.stringify({token_id:h})});if(!L.ok)throw new Error("http_"+L.status);await l(!0),d()}catch(L){s(t("xero-push-fail").replace("{err}",L.message),"error")}}async function m(h,w){const L=localStorage.getItem("mrpilot_token");w&&(w.disabled=!0);try{const S=await fetch("/api/erp/xero/auto-push",{method:"POST",headers:{Authorization:"Bearer "+L,"Content-Type":"application/json"},body:JSON.stringify({on:!!h})});if(!S.ok){let D="unknown";try{D=(await S.json()).detail||"unknown"}catch{}throw new Error(D)}s(h?t("erp-auto-push-toggled-on"):t("erp-auto-push-toggled-off"),"success"),n=!1,await l(!0),d()}catch(S){w&&(w.checked=!h),s(t("erp-auto-push-toggle-fail").replace("{err}",S.message||"network"),"error")}finally{w&&(w.disabled=!1)}}async function b(){const h=document.getElementById("drawer-history-save");if(!h||h.querySelector("#btn-xero-push")||h.querySelector("#pn-push-wrap")||(await l(!1),h.querySelector("#pn-push-wrap"))||h.querySelector("#btn-xero-push"))return;const w=r();if(!(w&&(w._historyId||w.history_id)))return;let S=!1,D="xero-push-tip";!e||!e.configured?(S=!0,D="xero-err-not_configured"):e.connected?u(w)&&(S=!0,D="xero-push-disabled-exc"):(S=!0,D="xero-push-disabled-no-conn");const B=document.createElement("button");B.type="button",B.id="btn-xero-push",B.className="btn btn-ghost"+(S?" disabled":""),B.disabled=S,B.title=t(D)||"",B.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg><span style="margin-left:4px;">'+o(t("xero-push-btn"))+"</span>",B.addEventListener("click",M);const P=document.getElementById("btn-push-erp");P&&P.parentNode?P.parentNode.insertBefore(B,P.nextSibling):h.insertBefore(B,h.firstChild)}async function M(){const h=r(),w=h&&(h._historyId||h.history_id);if(!w)return;const L=document.getElementById("btn-xero-push");L&&(L.disabled=!0,L.classList.add("loading"));const S=localStorage.getItem("mrpilot_token");try{const D=await fetch("/api/erp/xero/push/"+encodeURIComponent(w),{method:"POST",headers:{Authorization:"Bearer "+S}});if(!D.ok){let B="unknown";try{B=(await D.json()).detail||"unknown"}catch{}const P=String(B).replace(/^xero\./,"").toLowerCase(),Y=t("xero-"+P),G=Y&&Y!=="xero-"+P?Y:B;s(t("xero-push-fail").replace("{err}",G),"error");return}s(t("xero-push-ok"),"success")}catch(D){s(t("xero-push-fail").replace("{err}",D.message||"network"),"error")}finally{L&&(L.disabled=!1,L.classList.remove("loading"))}}async function I(){await l(!0),d(),x()}async function x(){const h=document.getElementById("erp-global-push-mode");if(!h)return;const w=localStorage.getItem("mrpilot_token");if(w)try{const L=await fetch("/api/settings/erp-push-mode",{headers:{Authorization:"Bearer "+w}});if(L.ok){const S=await L.json();S.mode&&(h.value=S.mode,h.dataset.prev=S.mode)}}catch{}}async function y(h){const w=h.value,L=localStorage.getItem("mrpilot_token");try{(await fetch("/api/settings/erp-push-mode",{method:"PUT",headers:{Authorization:"Bearer "+L,"Content-Type":"application/json"},body:JSON.stringify({mode:w})})).ok?(h.dataset.prev=w,s(t("pref-erp-mode-saved"),"success")):(h.value=h.dataset.prev||"smart",s(t("pref-save-failed"),"error"))}catch{h.value=h.dataset.prev||"smart",s(t("pref-save-failed"),"error")}}function $(){try{const h=String(window.location.hash||"");if(h.indexOf("xero=ok")>=0){const w=h.match(/n=(\d+)/),L=w?w[1]:"1";s((t("xero-toast-redirected-ok")||"").replace("{n}",L),"success"),history.replaceState(null,"",window.location.pathname+"#automation"),l(!0).then(d)}else h.indexOf("xero=err")>=0&&(s(t("xero-toast-redirected-err"),"error"),history.replaceState(null,"",window.location.pathname+"#automation"))}catch{}}function C(){if(a)return;a=!0,document.addEventListener("click",function(w){if(w.target.closest('.erp-subtab[data-erp-subtab="connect"]')){setTimeout(I,50);return}if(w.target.closest('.auto-nav-item[data-auto-tab="erp"]')){setTimeout(I,80);return}if(w.target.closest("#btn-xero-connect")){w.preventDefault(),c();return}if(w.target.closest("#btn-xero-disconnect")){w.preventDefault(),p();return}}),document.addEventListener("change",function(w){w.target&&w.target.matches('input[name="xero-default-org"]')&&f(w.target.value),w.target&&w.target.id==="xero-auto-push-toggle"&&m(w.target.checked,w.target),w.target&&w.target.id==="erp-global-push-mode"&&y(w.target)});const h=function(){return document.getElementById("drawer-body")};try{const w=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("btn-xero-push")&&b()}),L=h();if(L)w.observe(L,{childList:!0,subtree:!0});else{const S=new MutationObserver(function(){const D=h();D&&(w.observe(D,{childList:!0,subtree:!0}),S.disconnect())});S.observe(document.body,{childList:!0,subtree:!0})}}catch{}setTimeout($,500)}function F(){e&&d();const h=document.getElementById("btn-xero-push");if(h){const w=h.querySelector("span");w&&(w.textContent=t("xero-push-btn"))}}C(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("xero-adapter",F);async function j(h){const w=Date.now();for(;Date.now()-w<h;){if(typeof _userInfo<"u"&&_userInfo&&_userInfo.id)return _userInfo;await new Promise(L=>setTimeout(L,80))}return null}async function _(){await j(5e3);const h=document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]'),w=document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');h&&w&&await I()}setTimeout(_,200)})();(function(){const e={};function n(){if(document.getElementById("report-modal"))return;const d=`
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
        </div>`,c=document.createElement("div");c.innerHTML=d,document.body.appendChild(c.firstElementChild),document.getElementById("report-modal-close-x").addEventListener("click",a),document.getElementById("report-modal-cancel").addEventListener("click",a),document.getElementById("report-modal").addEventListener("click",p=>{p.target.id==="report-modal"&&a()})}function a(){const d=document.getElementById("report-modal");d&&(d.style.display="none"),o=null}let o=null;async function s(d,c){const p=d+":"+(c||"");if(e[p])return e[p];let f;try{const m=localStorage.getItem("mrpilot_token"),b=await fetch(`/api/reports/templates?lang=${encodeURIComponent(d)}`,{headers:{Authorization:"Bearer "+m}});if(!b.ok)throw new Error("templates fetch failed");f=(await b.json()).templates||[]}catch(m){console.error("fetchTemplates fail",m),f=[{code:"input_vat",name:t("tpl-input-vat"),desc:t("tpl-input-vat-desc"),recommended:!0},{code:"standard",name:t("tpl-standard"),desc:t("tpl-standard-desc"),recommended:!1},{code:"print",name:t("tpl-print"),desc:t("tpl-print-desc"),recommended:!1}]}if(f=f.filter(m=>m.code!=="erp"),c==="history-batch"){const m=f.findIndex(M=>M.code==="standard"),b=m>=0?m+1:f.length;f.splice(b,0,{code:"sales_detail_th",name:t("export-tpl-sales-detail"),desc:t("export-tpl-sales-detail-desc"),recommended:!1,is_new:!0})}return e[p]=f,f}function i(d){const c=document.getElementById("report-tpl-list"),p=d.map((m,b)=>`
            <label class="report-tpl-item${m.recommended?" is-recommended":""}">
                <input type="radio" name="report-tpl" value="${m.code}" ${m.recommended||b===0?"checked":""}>
                <div class="report-tpl-content">
                    <div class="report-tpl-name">
                        ${r(m.name)}
                        ${m.recommended?`<span class="report-tpl-badge">${r(t("report-recommended"))}</span>`:""}
                    </div>
                    <div class="report-tpl-desc">${r(m.desc||"")}</div>
                </div>
            </label>
        `).join(""),f=`
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
        `;c.innerHTML=p+f}function r(d){return d==null?"":String(d).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c])}function u(d){const c=new Date,p=c.getFullYear(),f=c.getMonth()+1;if(d==="all")return"all";if(d==="this-month")return`${p}-${String(f).padStart(2,"0")}`;if(d==="last-month"){const m=new Date(p,f-2,1);return`${m.getFullYear()}-${String(m.getMonth()+1).padStart(2,"0")}`}return d==="this-year"?`${p}`:d==="this-quarter"?`${p}-Q${Math.floor((f-1)/3)+1}`:"all"}window.openReportModal=async function(d){d=d||{},n(),typeof applyLang=="function"?applyLang(currentLang):document.querySelectorAll("#report-modal [data-i18n]").forEach(M=>{const I=M.getAttribute("data-i18n");I18N[currentLang]&&I18N[currentLang][I]&&(M.textContent=I18N[currentLang][I])});const c=document.getElementById("report-period-section");c&&(c.style.display=d.mode==="client"?"":"none");const p=document.getElementById("report-tpl-list");p.innerHTML=`<div class="report-tpl-loading">${r(t("report-modal-loading"))}</div>`,document.getElementById("report-modal").style.display="";const f=await s(currentLang,d&&d.mode);i(f),o=d;const m=document.getElementById("report-modal-download"),b=m.cloneNode(!0);m.parentNode.replaceChild(b,m),b.addEventListener("click",()=>l(o))};async function l(d){if(!d)return;const c=document.querySelector('input[name="report-tpl"]:checked');if(!c){showToast(t("report-toast-no-selection"),"info");return}const p=c.value,f=document.querySelector('input[name="report-period"]:checked'),m=f?f.value:"all",b=u(m),M=document.getElementById("report-modal-download"),I=M.innerHTML;M.disabled=!0,M.innerHTML=`<span>${r(t("report-modal-loading"))}</span>`;try{const x=localStorage.getItem("mrpilot_token");let y,$;if(d.mode==="records")y=await fetch("/api/reports/export",{method:"POST",headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify({template:p,lang:currentLang,records:d.records||[],meta:d.meta||{}})}),$=`mrpilot-${p}-${Date.now()}.xlsx`;else if(d.mode==="client"){const L=`/api/reports/clients/${d.clientId}/export?template=${encodeURIComponent(p)}&lang=${encodeURIComponent(currentLang)}&month=${encodeURIComponent(b)}`;y=await fetch(L,{headers:{Authorization:"Bearer "+x}}),$=`${(d.clientName||"client").replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40)}-${p}.xlsx`}else if(d.mode==="history-batch")p==="sales_detail_th"?(y=await fetch("/api/ocr/export-by-history-ids",{method:"POST",headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify({template:"sales_detail_th",lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),$=`Pearnly_SalesDetail_${Date.now()}.xlsx`):(y=await fetch("/api/reports/history/batch_export",{method:"POST",headers:{Authorization:"Bearer "+x,"Content-Type":"application/json"},body:JSON.stringify({template:p,lang:currentLang,history_ids:d.historyIds||[],client_id:d.clientId||null})}),$=`mrpilot-batch-${p}-${Date.now()}.xlsx`);else throw new Error("unknown mode: "+d.mode);if(!y.ok){let L="HTTP "+y.status;try{const S=await y.json();S&&S.detail&&(L=S.detail)}catch(S){console.warn("[batch-export] resp.json err.detail parse failed:",S)}y.status===404?showToast(t("report-toast-empty"),"info"):showToast(t("report-toast-fail")+" · "+L,"error");return}const C=await y.blob();let F=$;const _=(y.headers.get("Content-Disposition")||"").match(/filename\*=UTF-8''([^;]+)/i);if(_)try{F=decodeURIComponent(_[1])}catch{}const h=URL.createObjectURL(C),w=document.createElement("a");w.href=h,w.download=F,document.body.appendChild(w),w.click(),document.body.removeChild(w),URL.revokeObjectURL(h),showToast(t("report-toast-success"),"success"),a()}catch(x){console.error("doDownload fail",x),showToast(t("report-toast-fail")+" · "+(x.message||""),"error")}finally{M.disabled=!1,M.innerHTML=I}}document.addEventListener("DOMContentLoaded",()=>{const d=document.getElementById("btn-export");if(d){const p=d.cloneNode(!0);d.parentNode.replaceChild(p,d),p.addEventListener("click",()=>{if(typeof _results>"u"||!_results||_results.length===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"records",records:_results.map(f=>({filename:f.filename,merged_fields:f.merged_fields||{}}))})})}const c=document.getElementById("history-batch-export");c&&c.addEventListener("click",()=>{if(typeof _historySelected>"u"||_historySelected.size===0){showToast(t("report-toast-no-selection"),"info");return}openReportModal({mode:"history-batch",historyIds:Array.from(_historySelected)})})}),window.openClientExportModal=function(d,c){openReportModal({mode:"client",clientId:d,clientName:c||""})}})();(function(){const n=typeof window<"u"&&"showDirectoryPicker"in window,a=/\.(pdf|jpe?g|png|webp)$/i,o="mrpilot_folder_watcher",s=1;let i=null,r=null,u=null,l=60,d=!1,c=!1,p=0,f=0,m=0,b=[],M=null,I=!1;function x(){return i||(i=new Promise((k,T)=>{const A=indexedDB.open(o,s);A.onupgradeneeded=U=>{const z=U.target.result;z.objectStoreNames.contains("handles")||z.createObjectStore("handles"),z.objectStoreNames.contains("seen")||z.createObjectStore("seen"),z.objectStoreNames.contains("config")||z.createObjectStore("config")},A.onsuccess=U=>k(U.target.result),A.onerror=U=>T(U.target.error)}),i)}function y(k,T){return x().then(A=>new Promise((U,z)=>{const R=A.transaction(k,"readonly").objectStore(k).get(T);R.onsuccess=()=>U(R.result),R.onerror=()=>z(R.error)}))}function $(k,T,A){return x().then(U=>new Promise((z,v)=>{const R=U.transaction(k,"readwrite");R.objectStore(k).put(A,T),R.oncomplete=()=>z(),R.onerror=()=>v(R.error)}))}function C(k,T){return x().then(A=>new Promise((U,z)=>{const v=A.transaction(k,"readwrite");v.objectStore(k).delete(T),v.oncomplete=()=>U(),v.onerror=()=>z(v.error)}))}function F(k){return x().then(T=>new Promise((A,U)=>{const z=T.transaction(k,"readwrite");z.objectStore(k).clear(),z.oncomplete=()=>A(),z.onerror=()=>U(z.error)}))}async function j(k){if(!k)return!1;try{const T={mode:"read"};let A=await k.queryPermission(T);return A==="granted"?!0:(A=await k.requestPermission(T),A==="granted")}catch(T){return console.warn("[folder] permission check failed:",T),!1}}function _(k,T){const A=document.getElementById("folder-status-summary");A&&(A.setAttribute("data-i18n",k),A.textContent=t(k),A.className="auto-status-pill"+(T?" "+T:""))}function h(k){["folder-unsupported","folder-empty","folder-active"].forEach(T=>{const A=document.getElementById(T);A&&(A.style.display=T===k?"":"none")})}function w(k){if(!k)return"-";const T=k instanceof Date?k:new Date(k),A=String(T.getHours()).padStart(2,"0"),U=String(T.getMinutes()).padStart(2,"0"),z=String(T.getSeconds()).padStart(2,"0");return`${A}:${U}:${z}`}function L(){h("folder-active");const k=document.getElementById("folder-config-path");k&&r&&(k.textContent=r.name||"-");const T=document.getElementById("folder-interval-select");T&&(T.value=String(l)),document.getElementById("folder-stat-last").textContent=M?w(M):"-",document.getElementById("folder-stat-processed").textContent=String(p),document.getElementById("folder-stat-failed").textContent=String(f),document.getElementById("folder-stat-queue").textContent=String(m);const A=document.getElementById("btn-folder-pause"),U=document.getElementById("btn-folder-resume");A&&(A.style.display=d?"none":""),U&&(U.style.display=d?"":"none"),d?_("folder-status-paused","paused"):_("folder-status-running","running");const z=document.getElementById("folder-status-text");z&&(z.setAttribute("data-i18n",d?"folder-status-paused":"folder-status-running"),z.textContent=t(d?"folder-status-paused":"folder-status-running"));const v=document.getElementById("folder-status-pulse");v&&(v.className="folder-status-pulse"+(d?" paused":"")),S()}function S(){const k=document.getElementById("folder-recent-list");if(k){if(b.length===0){k.innerHTML=`<div class="folder-recent-empty">${escapeHtml(t("folder-recent-empty"))}</div>`;return}k.innerHTML=b.slice(0,20).map(T=>{let A;T.status==="ok"?A=`<span class="folder-recent-icon ok">${svgIcon("check",12)}</span>`:T.status==="dup"?A=`<span class="folder-recent-icon dup" title="${escapeHtml(t("folder-recent-dup"))}">${svgIcon("copy",12)}</span>`:T.status==="skip"?A=`<span class="folder-recent-icon skip" title="${escapeHtml(t("folder-recent-skip"))}">${svgIcon("minus",12)}</span>`:A=`<span class="folder-recent-icon fail">${svgIcon("alert",12)}</span>`;const U=T.status==="fail"&&T.error?T.error:T.status==="dup"&&T.reason||T.status==="skip"&&T.reason?T.reason:"",z=U?`<div class="folder-recent-err">${escapeHtml(U)}</div>`:"";return`
                <div class="folder-recent-item">
                    ${A}
                    <div class="folder-recent-body">
                        <div class="folder-recent-name">${escapeHtml(T.name)}</div>
                        ${z}
                    </div>
                    <div class="folder-recent-time">${w(T.time)}</div>
                </div>
            `}).join("")}}function D(k){b.unshift(k),b.length>50&&(b.length=50),$("config","recent_list",b).catch(()=>{})}async function B(k){const T=new FormData;T.append("file",k,k.name),T.append("source","folder");const A=await fetch("/api/ocr/recognize?source=folder",{method:"POST",headers:{Authorization:"Bearer "+token,"X-Source":"folder"},body:T});if(!A.ok){let U="http_"+A.status;try{const z=await A.json();U=z&&z.detail?typeof z.detail=="string"?z.detail:z.detail.code||JSON.stringify(z.detail):U}catch{}throw new Error(U)}return await A.json()}async function P(k){try{const A=(await k.getFile()).size;return await new Promise(z=>setTimeout(z,3e3)),(await k.getFile()).size===A&&A>0}catch{return!1}}async function Y(k,T,A,U){if(U>10)return;let z;try{z=await k.queryPermission({mode:"read"})}catch{z="denied"}if(z==="granted")for await(const v of k.values()){const R=T?`${T}/${v.name}`:v.name;if(v.kind==="file"){if(!a.test(v.name))continue;let O;try{O=await v.getFile()}catch{continue}const J=`${R}::${O.size}::${O.lastModified}`;if(await y("seen",J))continue;A.push({entry:v,file:O,seenKey:J,relPath:R})}else if(v.kind==="directory")try{await Y(v,R,A,U+1)}catch{}}}async function G(){if(!(c||d||!r)){c=!0;try{if(await r.queryPermission({mode:"read"})!=="granted"){console.warn("[folder] permission lost · stop"),K(),showToast("warn",t("folder-permission-lost"));return}M=new Date;const T=[];await Y(r,"",T,0),m=T.length,L();for(const A of T){if(d)break;if(!await P(A.entry)){m=Math.max(0,m-1),L();continue}try{let z;try{z=await A.entry.getFile()}catch{z=A.file}const v=await B(z);await $("seen",A.seenKey,{name:z.name,relPath:A.relPath,size:z.size,lastModified:z.lastModified,processed_at:Date.now()});const R=v.history_ids||(v.history_id?[v.history_id]:[]),O=v.duplicate_warnings||[],J=A.relPath||z.name;R.length>0?(p+=R.length,D({name:J,status:"ok",time:new Date,history_id:R[0],count:R.length}),await $("config","processed_count",p)):O.length>0?D({name:J,status:"dup",time:new Date,reason:t("folder-recent-dup-reason")}):D({name:J,status:"skip",time:new Date,reason:t("folder-recent-skip-reason")})}catch(z){f++,D({name:A.relPath||A.file.name,status:"fail",time:new Date,error:String(z.message||z)}),await $("config","failed_count",f)}m=Math.max(0,m-1),L()}}catch(k){console.warn("[folder] scan error:",k)}finally{c=!1,L()}}}function W(){u&&clearInterval(u),u=setInterval(G,l*1e3)}function te(){u&&(clearInterval(u),u=null)}function re(k){if(!r||d)return;const T=typeof t=="function"?t("folder-unload-warn"):"Folder watcher running · close anyway?";return k.preventDefault(),k.returnValue=T,T}function H(){window._pearnlyFolderUnloadAttached||(window._pearnlyFolderUnloadAttached=!0,window.addEventListener("beforeunload",re))}function E(){window._pearnlyFolderUnloadAttached&&(window._pearnlyFolderUnloadAttached=!1,window.removeEventListener("beforeunload",re))}function g(){d=!1,W(),H(),L(),G()}function q(){d=!0,te(),E(),L()}function N(){d=!1,W(),H(),L(),G()}function K(){d=!0,te(),E()}async function Z(){try{const k=await window.showDirectoryPicker({mode:"read",startIn:"documents"});if(!await j(k)){showToast("warn",t("folder-permission-denied"));return}r=k,await $("handles","main",k),p=0,f=0,m=0,b=[],await $("config","processed_count",0),await $("config","failed_count",0),await F("seen"),g()}catch(k){k&&k.name!=="AbortError"&&console.warn("[folder] pick failed:",k)}}async function le(){await showConfirm(t("folder-confirm-remove"),{danger:!0})&&(K(),r=null,p=0,f=0,m=0,b=[],await C("handles","main"),await C("config","processed_count"),await C("config","failed_count"),await F("seen"),h("folder-empty"),_("folder-status-empty",""))}async function ie(){b=[];try{await C("config","recent_list")}catch{}S()}async function V(){if(I)return;if(I=!0,!n){h("folder-unsupported"),_("folder-status-unsupported",""),ne();return}Q();let k=null;try{k=await y("handles","main")}catch{}if(!k){h("folder-empty"),_("folder-status-empty","");return}if(!await j(k)){h("folder-empty"),_("folder-status-empty",""),await C("handles","main"),showToast("warn",t("folder-permission-lost-restart"));return}r=k;try{p=await y("config","processed_count")||0}catch{}try{f=await y("config","failed_count")||0}catch{}try{const A=await y("config","recent_list");Array.isArray(A)&&(b=A.map(U=>({...U,time:U.time?new Date(U.time):new Date})))}catch{}g()}function Q(){const k=document.getElementById("btn-folder-pick"),T=document.getElementById("btn-folder-pause"),A=document.getElementById("btn-folder-resume"),U=document.getElementById("btn-folder-scan-now"),z=document.getElementById("btn-folder-remove"),v=document.getElementById("btn-folder-clear-recent"),R=document.getElementById("folder-interval-select");k&&k.addEventListener("click",Z),T&&T.addEventListener("click",q),A&&A.addEventListener("click",N),U&&U.addEventListener("click",()=>{G()}),z&&z.addEventListener("click",le),v&&v.addEventListener("click",ie),R&&R.addEventListener("change",O=>{l=parseInt(O.target.value,10)||60,d||W()}),ee()}function ee(){document.querySelectorAll('[data-auto-panel="folder"] [data-tab-jump]').forEach(k=>{k.dataset.tabJumpBound||(k.dataset.tabJumpBound="1",k.addEventListener("click",T=>{const A=T.currentTarget.dataset.tabJump;if(A==="email")typeof switchAutomationTab=="function"&&switchAutomationTab("email");else if(A==="upload"){const U=document.querySelector('[data-page="recognize"]')||document.querySelector('[data-page="upload"]');U&&U.click()}}))})}function ne(){ee()}window._loadFolderWatcherPanel=V;function oe(){try{if(navigator.userAgentData&&Array.isArray(navigator.userAgentData.brands))return navigator.userAgentData.brands.some(T=>/chromium|google chrome|microsoft edge/i.test(T.brand||""))}catch{}const k=navigator.userAgent||"";return!!(/Edg\//.test(k)||/Chrome\//.test(k)&&!/OPR\/|YaBrowser|Opera/.test(k))}function ue(){try{if(oe()||localStorage.getItem("pearnly_chrome_banner_dismissed")==="1")return;const k=document.getElementById("chrome-only-banner");if(!k)return;const T=k.querySelector('[data-i18n="chrome-banner-msg"]'),A=k.querySelector('[data-i18n="chrome-banner-dismiss"]');T&&typeof t=="function"&&(T.textContent=t("chrome-banner-msg")),A&&typeof t=="function"&&(A.textContent=t("chrome-banner-dismiss")),k.style.display="";const U=document.getElementById("chrome-only-banner-close");U&&!U.dataset.bound&&(U.dataset.bound="1",U.addEventListener("click",()=>{k.style.display="none";try{localStorage.setItem("pearnly_chrome_banner_dismissed","1")}catch{}}))}catch{}}typeof document<"u"&&(document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ue):setTimeout(ue,0)),window._refreshChromeBanner=ue})();(function(){let e=null,n=null,a="new",o=!1,s=!1;async function i(){const B=document.getElementById("email-empty"),P=document.getElementById("email-account-card");if(document.getElementById("email-logs-section"),!(!B||!P))try{const Y=await fetch("/api/email-ingest/account",{headers:{Authorization:"Bearer "+token}});if(Y.status===401){localStorage.removeItem("mrpilot_token");const W=await Y.json().catch(()=>({}));if((typeof W.detail=="string"?W.detail:W.detail&&W.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}if(!Y.ok){u("none");return}const G=await Y.json();e=G.account||null,n=G.presets||{},o=!0,r(),e&&w()}catch(Y){console.error("[email-ingest] load failed",Y),u("none")}}function r(){const B=document.getElementById("email-empty"),P=document.getElementById("email-account-card"),Y=document.getElementById("email-logs-section");if(!e){B.style.display="",P.style.display="none",Y&&(Y.style.display="none"),u("none");return}B.style.display="none",P.style.display="",Y&&(Y.style.display="");const G=document.getElementById("email-account-addr"),W=document.getElementById("email-account-host"),te=document.getElementById("email-account-last"),re=document.getElementById("email-last-error"),H=document.getElementById("email-enabled-toggle");if(G&&(G.textContent=e.email_address||"-"),W&&(W.textContent=`${e.imap_host||"-"}:${e.imap_port||993}`),te){const E=e.last_fetched_at;if(!E)te.textContent=t("email-last-never");else{const g=l(E),q=!e.last_error;te.textContent=q?t("email-last-ok",{time:g}):t("email-last-fail",{time:g})}}re&&(e.last_error?(re.style.display="",re.textContent=d(e.last_error)):re.style.display="none"),H&&(H.checked=!!e.enabled),e.enabled?e.last_error?u("error"):u("on"):u("off")}function u(B){const P=document.getElementById("email-status-summary");if(!P)return;P.classList.remove("none","ready","active","coming");let Y="auto-status-loading";B==="none"?(Y="email-status-none",P.classList.add("none")):B==="on"?(Y="email-status-on",P.classList.add("active")):B==="off"?(Y="email-status-off",P.classList.add("coming")):B==="error"&&(Y="email-status-error",P.classList.add("none")),P.setAttribute("data-i18n",Y),P.textContent=t(Y)}function l(B){if(!B)return"";const P=new Date(B);if(isNaN(P.getTime()))return"";const Y=G=>String(G).padStart(2,"0");return`${Y(P.getMonth()+1)}-${Y(P.getDate())} ${Y(P.getHours())}:${Y(P.getMinutes())}`}function d(B){if(!B)return"";const P=String(B);return/auth|AUTHENTICATIONFAILED|invalid credentials/i.test(P)?t("email-test-auth-fail"):/timeout|timed out/i.test(P)?t("email.timeout"):(/ENOTFOUND|getaddrinfo/i.test(P),P)}function c(B){a=B;const P=document.getElementById("email-modal");if(!P)return;const Y=document.getElementById("email-preset");Y.innerHTML="";const G=n||{},W=["gmail","outlook","yahoo","icloud","qq","163","custom"],te={gmail:"Gmail",outlook:"Outlook / Office365",yahoo:"Yahoo Mail",icloud:"iCloud",qq:"QQ 邮箱",163:"网易 163"};W.forEach(Q=>{if(!G[Q])return;const ee=document.createElement("option");ee.value=Q,ee.textContent=Q==="custom"?t("email-preset-custom"):te[Q]||Q,Y.appendChild(ee)});const re=document.getElementById("email-modal-title"),H=document.getElementById("email-address"),E=document.getElementById("email-password"),g=document.getElementById("email-imap-host"),q=document.getElementById("email-imap-port"),N=document.getElementById("email-imap-ssl"),K=document.getElementById("email-folder"),Z=document.getElementById("email-mark-read"),le=document.getElementById("email-bind-enabled"),ie=document.getElementById("email-test-result"),V=document.getElementById("email-adv-details");if(ie&&(ie.style.display="none",ie.textContent=""),B==="edit"&&e){re.setAttribute("data-i18n","email-modal-title-edit"),re.textContent=t("email-modal-title-edit"),H.value=e.email_address||"",E.value="",E.setAttribute("data-i18n-placeholder","email-field-password-edit-ph"),E.placeholder=t("email-field-password-edit-ph"),g.value=e.imap_host||"",q.value=e.imap_port||993,N.checked=e.imap_use_ssl!==!1,K.value=e.folder||"INBOX",Z.checked=e.mark_as_read!==!1,le.checked=e.enabled!==!1;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=e.filter_sender||""),ee&&(ee.value=e.filter_subject||""),y(e.interval_min||15),Y.value=M(e.imap_host)||"custom",V&&(V.open=!0)}else{re.setAttribute("data-i18n","email-modal-title-new"),re.textContent=t("email-modal-title-new"),H.value="",E.value="",E.setAttribute("data-i18n-placeholder","email-field-password-ph"),E.placeholder=t("email-field-password-ph"),Y.value="gmail",f("gmail"),K.value="INBOX",Z.checked=!0,le.checked=!0;const Q=document.getElementById("email-filter-sender"),ee=document.getElementById("email-filter-subject");Q&&(Q.value=""),ee&&(ee.value=""),y(15),V&&(V.open=!1)}x(),P.style.display="flex",setTimeout(()=>H.focus(),60)}function p(){const B=document.getElementById("email-modal");B&&(B.style.display="none")}function f(B){const P=(n||{})[B];if(!P||B==="custom")return;const Y=document.getElementById("email-imap-host"),G=document.getElementById("email-imap-port"),W=document.getElementById("email-imap-ssl");Y&&(Y.value=P.host||""),G&&(G.value=P.port||993),W&&(W.checked=P.ssl!==!1)}const m={"gmail.com":"gmail","googlemail.com":"gmail","outlook.com":"outlook","hotmail.com":"outlook","live.com":"outlook","office365.com":"outlook","msn.com":"outlook","yahoo.com":"yahoo","yahoo.co.jp":"yahoo","icloud.com":"icloud","me.com":"icloud","mac.com":"icloud","qq.com":"qq","foxmail.com":"qq","163.com":"163","126.com":"163","yeah.net":"163"};function b(B){if(!B||!B.includes("@"))return;const P=B.split("@")[1].toLowerCase().trim(),Y=m[P];if(!Y)return;const G=document.getElementById("email-preset");if(!G)return;const W=G.value;W&&W!=="custom"&&W!==""&&W===Y||(G.value=Y,f(Y))}function M(B){if(!B)return null;const P=n||{};for(const Y in P)if(Y!=="custom"&&P[Y]&&P[Y].host===B)return Y;return null}function I(){const B=document.querySelector("#email-interval-options .email-interval-btn.active"),P=B?parseInt(B.dataset.interval,10):15;return{email_address:(document.getElementById("email-address").value||"").trim(),password:document.getElementById("email-password").value||"",imap_host:(document.getElementById("email-imap-host").value||"").trim(),imap_port:parseInt(document.getElementById("email-imap-port").value||"993",10)||993,imap_use_ssl:document.getElementById("email-imap-ssl").checked,folder:(document.getElementById("email-folder").value||"INBOX").trim()||"INBOX",mark_as_read:document.getElementById("email-mark-read").checked,enabled:document.getElementById("email-bind-enabled").checked,interval_min:[5,15,60].includes(P)?P:15,filter_sender:(document.getElementById("email-filter-sender").value||"").trim()||null,filter_subject:(document.getElementById("email-filter-subject").value||"").trim()||null}}function x(){const B=document.getElementById("email-interval-options");!B||B._bound||(B._bound=!0,B.addEventListener("click",P=>{const Y=P.target.closest(".email-interval-btn");Y&&(B.querySelectorAll(".email-interval-btn").forEach(G=>G.classList.remove("active")),Y.classList.add("active"))}))}function y(B){const P=[5,15,60].includes(B)?B:15,Y=document.getElementById("email-interval-options");Y&&Y.querySelectorAll(".email-interval-btn").forEach(G=>{G.classList.toggle("active",parseInt(G.dataset.interval,10)===P)})}function $(B,P){const Y=document.getElementById("email-test-result");Y&&(Y.style.display="",Y.textContent=P,Y.className="form-test-result "+(B==="ok"?"ok":B==="running"?"running":"fail"))}async function C(){const B=I();if(!B.email_address){$("fail",t("email-addr-required"));return}if(!B.password){$("fail",t("email-password-required"));return}if(!B.imap_host){$("fail",t("email-host-required"));return}const P=document.getElementById("btn-email-modal-test");P&&(P.disabled=!0),$("running",t("email-test-running"));try{const Y=await fetch("/api/email-ingest/test",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:B.email_address,password:B.password,imap_host:B.imap_host,imap_port:B.imap_port,imap_use_ssl:B.imap_use_ssl,folder:B.folder})}),G=await Y.json().catch(()=>({}));if(Y.ok&&G.success)$("ok",t("email-test-ok",{folder:B.folder,n:G.folder_count??"?"}));else{const W=G.error_msg||"";W==="auth_failed"||/auth/i.test(W)?$("fail",t("email-test-auth-fail")):$("fail",t("email-test-fail",{msg:W||Y.status}))}}catch(Y){$("fail",t("email-test-fail",{msg:String(Y).slice(0,120)}))}finally{P&&(P.disabled=!1)}}async function F(){const B=I();if(!B.email_address){$("fail",t("email-addr-required"));return}if(a==="new"&&!B.password){$("fail",t("email-password-required"));return}if(!B.imap_host){$("fail",t("email-host-required"));return}const P=document.getElementById("btn-email-modal-save");P&&(P.disabled=!0);const Y={...B};a==="edit"&&!Y.password&&delete Y.password;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(Y)}),W=await G.json().catch(()=>({}));if(G.ok&&W.ok)e=W.account,showToast(t("email-save-ok"),"success"),p(),r(),w();else{const re="email."+(W.detail||"").split(".").slice(-1)[0];$("fail",t(re)!==re?t(re):t("email-save-fail"))}}catch{$("fail",t("email-save-fail"))}finally{P&&(P.disabled=!1)}}async function j(){if(!(!e||!await showConfirm(t("email-unbind-confirm",{email:e.email_address}),{danger:!0,okText:t("email-btn-unbind")})))try{if((await fetch("/api/email-ingest/account",{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){e=null,showToast(t("email-unbind-ok"),"success"),r();const Y=document.getElementById("email-logs-list");Y&&(Y.innerHTML="")}else showToast(t("email-unbind-fail"),"error")}catch{showToast(t("email-unbind-fail"),"error")}}async function _(){if(!e||s)return;if(!e.enabled){showToast(t("email.disabled"),"error");return}s=!0;const B=document.getElementById("btn-email-trigger"),P=B?B.innerHTML:"";B&&(B.disabled=!0,B.innerHTML=`<span>${escapeHtml(t("email-trigger-running"))}</span>`);try{const Y=await fetch("/api/email-ingest/trigger",{method:"POST",headers:{Authorization:"Bearer "+token}}),G=await Y.json().catch(()=>({}));if(Y.ok){const W=G.emails_scanned||0,te=G.ocr_succeeded||0,re=G.ocr_failed||0;W===0&&te===0&&re===0?showToast(t("email-trigger-empty"),"success"):showToast(t("email-trigger-result",{scanned:W,ok:te,fail:re}),re>0?"warn":"success")}else{const te="email."+(G.detail||"").split(".").slice(-1)[0];showToast(t(te)!==te?t(te):t("email-trigger-fail"),"error")}await i()}catch{showToast(t("email-trigger-fail"),"error")}finally{s=!1,B&&(B.disabled=!1,B.innerHTML=P)}}async function h(){if(!e)return;const B=document.getElementById("email-enabled-toggle"),P=!!(B&&B.checked),Y=e.enabled;try{const G=await fetch("/api/email-ingest/account",{method:"PUT",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({email_address:e.email_address,imap_host:e.imap_host,imap_port:e.imap_port,imap_use_ssl:e.imap_use_ssl,folder:e.folder||"INBOX",filter_subject:e.filter_subject||null,filter_sender:e.filter_sender||null,mark_as_read:e.mark_as_read!==!1,enabled:P})}),W=await G.json().catch(()=>({}));G.ok&&W.ok?(e=W.account,r()):(B&&(B.checked=Y),showToast(t("email-toggle-fail"),"error"))}catch{B&&(B.checked=Y),showToast(t("email-toggle-fail"),"error")}}async function w(){const B=document.getElementById("email-logs-list");if(B){B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`;try{const P=await fetch("/api/email-ingest/logs?limit=20",{headers:{Authorization:"Bearer "+token}});if(!P.ok){B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const Y=await P.json();if(!Array.isArray(Y)||Y.length===0){B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("email-logs-empty"))}</div>`;return}B.innerHTML=Y.map(L).join("")}catch{B.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}function L(B){const P=l(B.created_at),Y=B.status||"failed",G=Y==="success"?"ok":Y==="partial"?"partial":"fail",W=Y==="success"?"✓":Y==="partial"?"◐":"✗",te=B.trigger==="manual"?`<span class="log-tag manual">${escapeHtml(t("email-log-tag-manual"))}</span>`:`<span class="log-tag auto">${escapeHtml(t("email-log-tag-auto"))}</span>`,re=t("email-log-counts",{scanned:B.emails_scanned||0,att:B.attachments_found||0,ok:B.ocr_succeeded||0,fail:B.ocr_failed||0}),H=(B.elapsed_ms||0)+"ms";return`
            <div class="email-log-row ${G}">
                <span class="log-time">${escapeHtml(P)}</span>
                <span class="log-status">${W}</span>
                ${te}
                <span class="log-counts">${escapeHtml(re)}</span>
                <span class="log-elapsed">${escapeHtml(H)}</span>
            </div>
        `}function S(){const B=document.getElementById("btn-email-bind");B&&B.addEventListener("click",()=>c("new"));const P=document.getElementById("btn-email-edit");P&&P.addEventListener("click",()=>c("edit"));const Y=document.getElementById("btn-email-unbind");Y&&Y.addEventListener("click",j);const G=document.getElementById("btn-email-trigger");G&&G.addEventListener("click",_);const W=document.getElementById("email-enabled-toggle");W&&W.addEventListener("change",h);const te=document.getElementById("email-modal-close");te&&te.addEventListener("click",p);const re=document.getElementById("btn-email-modal-cancel");re&&re.addEventListener("click",p);const H=document.getElementById("btn-email-modal-test");H&&H.addEventListener("click",C);const E=document.getElementById("btn-email-modal-save");E&&E.addEventListener("click",F);const g=document.getElementById("email-preset");g&&g.addEventListener("change",K=>f(K.target.value));const q=document.getElementById("email-address");q&&!q.dataset.autoBound&&(q.dataset.autoBound="1",q.addEventListener("blur",K=>b((K.target.value||"").trim())),q.addEventListener("input",K=>{const Z=(K.target.value||"").trim();Z.includes("@")&&Z.split("@")[1].includes(".")&&b(Z)}));const N=document.getElementById("btn-email-refresh-logs");N&&N.addEventListener("click",()=>{N.classList.add("spinning"),setTimeout(()=>N.classList.remove("spinning"),600),w()})}S(),window._loadEmailIngestPanel=i,window._rerenderEmailIngest=function(){if(!o)return;r();const B=document.getElementById("email-logs-section");e&&B&&B.open&&w()};let D=null;window._startEmailLogAutoRefresh=function(){D||(D=setInterval(()=>{e&&o&&w()},3e4))},window._stopEmailLogAutoRefresh=function(){D&&(clearInterval(D),D=null)}})();(function(){let e=[],n=null,a=[],o="all",s=null,i=!1;async function r(){if(i){S();return}i=!0,u(),await l(),S()}function u(){const v=document.getElementById("bank-file-input");v&&!v._bound&&(v._bound=!0,v.addEventListener("change",b));const R=document.getElementById("btn-bank-queue-clear-done");R&&!R._bound&&(R._bound=!0,R.addEventListener("click",C));const O=document.getElementById("btn-bank-back");O&&!O._bound&&(O._bound=!0,O.addEventListener("click",()=>{n=null,a=[],te()}));const J=document.getElementById("btn-bank-delete");J&&!J._bound&&(J._bound=!0,J.addEventListener("click",h));const X=document.getElementById("btn-bank-run-match");X&&!X._bound&&(X._bound=!0,X.addEventListener("click",_)),document.querySelectorAll(".bank-filter-btn").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{o=fe.dataset.bankFilter||"all",document.querySelectorAll(".bank-filter-btn").forEach(me=>{me.classList.toggle("active",me===fe)}),Z()}))}),document.querySelectorAll("[data-bank-cand-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",ne))});const de=document.getElementById("btn-bank-cand-pane-close");de&&!de._bound&&(de._bound=!0,de.addEventListener("click",ne));const se=document.getElementById("btn-bank-cand-ignore");se&&!se._bound&&(se._bound=!0,se.addEventListener("click",w));const ce=document.getElementById("btn-bank-cand-ignore-pane");ce&&!ce._bound&&(ce._bound=!0,ce.addEventListener("click",w));const ae=document.getElementById("bank-client-badge");ae&&!ae._bound&&(ae._bound=!0,ae.addEventListener("click",E)),document.querySelectorAll("[data-bank-client-picker-close]").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",g))});const pe=document.getElementById("btn-bank-client-picker-save");pe&&!pe._bound&&(pe._bound=!0,pe.addEventListener("click",N)),document.querySelectorAll(".bank-sessions-chip").forEach(fe=>{fe._bound||(fe._bound=!0,fe.addEventListener("click",()=>{D=fe.dataset.sessFilter||"all",document.querySelectorAll(".bank-sessions-chip").forEach(me=>{me.classList.toggle("active",me===fe)}),B()}))})}async function l(){try{const v=await fetch("/api/bank-recon/sessions?limit=30",{headers:{Authorization:"Bearer "+token}});if(!v.ok)throw new Error("sessions:"+v.status);e=await v.json(),B()}catch(v){console.warn("[bank-recon] loadSessions failed",v),e=[],B()}}async function d(v){try{const R="/api/bank-recon/sessions/"+encodeURIComponent(v)+(o!=="all"?"?filter="+o:""),O=await fetch(R,{headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("detail:"+O.status);const J=await O.json();n=J.session,a=J.transactions||[],W()}catch(R){console.warn("[bank-recon] loadSessionDetail failed",R),showToast(t("bank-load-failed"),"error")}}let c=[],p=0;const f=3;function m(){return p+=1,"q"+p+"_"+Date.now()}async function b(v){const R=Array.from(v.target.files||[]);if(v.target.value="",R.length!==0){for(const O of R){const J={id:m(),file:O,name:O.name,size:O.size,status:"pending",progress:0,error_code:null,tx_count:0,session_id:null};O.name.toLowerCase().endsWith(".pdf")?O.size>20*1024*1024&&(J.status="failed",J.error_code="bank_recon.file_too_large"):(J.status="failed",J.error_code="bank_recon.only_pdf"),c.push(J)}M(),I(),F()}}function M(){const v=document.getElementById("bank-upload-queue");v&&(v.style.display=""),oe(),ue()}function I(){const v=document.getElementById("bank-upload-queue-list"),R=document.getElementById("bank-upload-queue-summary");if(!v)return;if(c.length===0){v.innerHTML="",R&&(R.textContent="");const se=document.getElementById("bank-upload-queue");se&&(se.style.display="none");return}let O=0,J=0,X=0,de=0;for(const se of c)se.status==="ok"?O++:se.status==="failed"?J++:se.status==="uploading"||se.status==="parsing"?X++:de++;R&&(R.textContent=t("bank-queue-summary").replace("{ok}",O).replace("{run}",X).replace("{wait}",de).replace("{fail}",J)),v.innerHTML=c.map(x).join(""),v.querySelectorAll("[data-q-act]").forEach(se=>{const ce=se.dataset.qAct,ae=se.dataset.qId;se.addEventListener("click",()=>{ce==="retry"&&y(ae),ce==="remove"&&$(ae)})})}function x(v){const R=(v.size/1024).toFixed(0)+" KB";let O="",J="";if(v.status==="pending")O='<span class="bq-stat bq-wait">'+t("bank-queue-status-wait")+"</span>",J='<button data-q-act="remove" data-q-id="'+z(v.id)+'" class="bq-act">×</button>';else if(v.status==="uploading")O='<span class="bq-stat bq-run">'+t("bank-queue-status-uploading")+'</span><div class="bq-bar"><div class="bq-bar-fill" style="width:'+(v.progress||0)+'%"></div></div>';else if(v.status==="parsing")O='<span class="bq-stat bq-run">'+t("bank-queue-status-parsing")+'</span><div class="bq-bar"><div class="bq-bar-fill bq-bar-indet"></div></div>';else if(v.status==="ok")O='<span class="bq-stat bq-ok">'+t("bank-queue-status-ok").replace("{n}",v.tx_count||0)+"</span>",J='<button data-q-act="remove" data-q-id="'+z(v.id)+'" class="bq-act">×</button>';else if(v.status==="failed"){const X=k(v.error_code||"unknown");O='<span class="bq-stat bq-fail" title="'+z(X)+'">'+z(X)+"</span>",J='<button data-q-act="retry" data-q-id="'+z(v.id)+'" class="bq-act bq-act-retry">'+t("bank-queue-retry")+'</button><button data-q-act="remove" data-q-id="'+z(v.id)+'" class="bq-act">×</button>'}return'<div class="bq-row" data-q-row="'+z(v.id)+'"><div class="bq-name" title="'+z(v.name)+'">'+z(v.name)+'</div><div class="bq-size">'+R+'</div><div class="bq-status">'+O+'</div><div class="bq-actions">'+J+"</div></div>"}function y(v){const R=c.find(O=>O.id===v);R&&(R.status="pending",R.error_code=null,R.progress=0,I(),F())}function $(v){const R=c.findIndex(J=>J.id===v);if(R<0)return;const O=c[R];O.status==="uploading"||O.status==="parsing"||(c.splice(R,1),I())}function C(){c=c.filter(v=>v.status!=="ok"),I()}async function F(){for(;;){if(c.filter(O=>O.status==="uploading"||O.status==="parsing").length>=f)return;const R=c.find(O=>O.status==="pending");if(!R){c.every(O=>O.status==="ok"||O.status==="failed")&&(await l(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage());return}j(R).then(()=>F())}}async function j(v){v.status="uploading",v.progress=0,I();try{const R=new FormData;R.append("file",v.file,v.name);const O=await new Promise((X,de)=>{const se=new XMLHttpRequest;se.open("POST","/api/bank-recon/upload"),se.setRequestHeader("Authorization","Bearer "+token),se.upload.onprogress=ce=>{ce.lengthComputable&&(v.progress=Math.min(99,Math.round(ce.loaded/ce.total*100)),I())},se.upload.onload=()=>{v.status="parsing",I()},se.onload=()=>{se.status>=200&&se.status<300?X({status:se.status,text:se.responseText}):X({status:se.status,text:se.responseText})},se.onerror=()=>de(new Error("network")),se.send(R)});let J={};try{J=JSON.parse(O.text||"{}")}catch{J={}}if(O.status>=400){v.status="failed",v.error_code=J&&J.detail||"unknown",I();return}if(J.parse_status==="parse_failed"){v.status="failed",v.error_code=J.error==="scanned_pdf_not_yet"?"bank_recon.scanned":"bank_recon.no_tx",I();return}v.status="ok",v.tx_count=J.tx_count||0,v.session_id=J.session_id||null,I()}catch(R){console.warn("[bank-recon] upload failed",R),v.status="failed",v.error_code="network",I()}}async function _(){if(!n)return;const v=document.getElementById("btn-bank-run-match"),R=v.innerHTML;v.disabled=!0,v.innerHTML="<span>"+t("bank-matching")+"</span>";try{const O=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/match",{method:"POST",headers:{Authorization:"Bearer "+token}});if(!O.ok)throw new Error("match:"+O.status);const J=await O.json();showToast(t("bank-match-done").replace("{matched}",J.matched).replace("{suggested}",J.suggested).replace("{unmatched}",J.unmatched),"success"),await d(n.id),await l()}catch(O){console.warn("[bank-recon] match failed",O),showToast(t("bank-match-failed"),"error")}finally{v.disabled=!1,v.innerHTML=R}}async function h(){if(!(!n||!await showConfirm(t("bank-delete-confirm"),{danger:!0})))try{const R=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!R.ok)throw new Error("delete:"+R.status);showToast(t("bank-deleted"),"success"),n=null,a=[],te(),await l()}catch(R){console.warn("[bank-recon] delete failed",R),showToast(t("bank-delete-failed"),"error")}}async function w(){if(s)try{const v=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"ignored"})});if(!v.ok)throw new Error("ignore:"+v.status);ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}}async function L(v){if(s)try{const R=await fetch("/api/bank-recon/tx/"+encodeURIComponent(s.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"matched",history_id:v})});if(!R.ok)throw new Error("pick:"+R.status);showToast(t("bank-matched-ok"),"success"),ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}}function S(){const v=document.getElementById("bank-status-summary");if(!v)return;if(e.length===0){v.textContent=t("bank-pill-none");return}let O=0;for(const J of e)J.parse_status==="parsed"&&(J.unmatched_count||0)>0&&O++;v.textContent=O>0?t("bank-pill-pending").replace("{n}",O):t("bank-pill-ok")}let D="all";function B(){const v=document.getElementById("bank-sessions-list");if(!v)return;let R=e||[];if(D==="parsed"?R=R.filter(O=>O.parse_status==="parsed"):D==="failed"&&(R=R.filter(O=>O.parse_status==="parse_failed")),!e||e.length===0){v.innerHTML='<div class="bank-empty" data-i18n="bank-sessions-empty">'+t("bank-sessions-empty")+"</div>";return}if(R.length===0){v.innerHTML='<div class="bank-empty">'+t("bank-sess-filter-empty")+"</div>";return}v.innerHTML=R.map(O=>Y(O)).join(""),v.querySelectorAll(".bank-session-row").forEach(O=>{O.addEventListener("click",J=>{J.target.closest(".bank-session-trash")||d(O.dataset.sessionId)})}),v.querySelectorAll(".bank-session-trash").forEach(O=>{O.addEventListener("click",J=>{J.stopPropagation();const X=O.dataset.sessionId,de=O.dataset.sessionName||"";P(X,de)})})}async function P(v,R){if(!v)return;const O=(t("bank-session-delete-confirm")||"确定删除这条对账记录吗?").replace("{name}",R||"");if(await showConfirm(O,{danger:!0}))try{const X=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(v),{method:"DELETE",headers:{Authorization:"Bearer "+token}});if(!X.ok)throw new Error("delete:"+X.status);showToast(t("bank-deleted"),"success"),n&&n.id===v&&(n=null,a=[],te()),await l(),typeof window.loadReconcilePage=="function"&&window.loadReconcilePage()}catch(X){console.warn("[bank-recon] delete failed",X),showToast(t("bank-delete-failed"),"error")}}window._deleteBankSession=P;function Y(v){const R=(v.bank_code||"OTHER").toUpperCase(),O=U(v.period_start,v.period_end),J=v.account_last4?"···"+v.account_last4:"",X=G(v),de=A(v.created_at);return`
            <div class="bank-session-row" data-session-id="${z(v.id)}">
                <div class="bank-session-bank bk-${z(R)}">${z(R)}</div>
                <div class="bank-session-info">
                    <div class="bank-session-title">${z(v.source_filename||O||"-")}</div>
                    <div class="bank-session-meta">${z(O)} · ${z(J)} · ${z(de)}</div>
                </div>
                <div class="bank-session-counts">${X}</div>
                <button class="bank-session-trash" data-session-id="${z(v.id)}" data-session-name="${z(v.source_filename||"")}" title="${z(t("bank-session-delete-tip")||"删除")}">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                    </svg>
                </button>
                <div class="bank-session-arrow">
                    <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
                </div>
            </div>
        `}function G(v){if(v.parse_status==="parse_failed")return`<span class="bank-session-count cnt-failed">${t("bank-count-parse-failed")}</span>`;if(v.parse_status!=="parsed")return`<span class="bank-session-count">${t("bank-count-parsing")}</span>`;const R=v.tx_count||0,O=v.matched_count||0,J=v.unmatched_count||0,X=[`<span class="bank-session-count">${R} ${t("bank-count-tx")}</span>`];return O>0&&X.push(`<span class="bank-session-count cnt-matched">${O} ${t("bank-count-matched")}</span>`),J>0&&X.push(`<span class="bank-session-count cnt-unmatched">${J} ${t("bank-count-unmatched")}</span>`),X.join("")}function W(){document.getElementById("bank-detail").style.display="",document.querySelector(".bank-sessions-section").style.display="none",K(),Z(),re()}function te(){document.getElementById("bank-detail").style.display="none",document.querySelector(".bank-sessions-section").style.display="";const v=document.getElementById("bank-detail-body");v&&v.classList.remove("has-pane"),s=null}function re(){const v=document.getElementById("bank-client-badge");if(!v||!n)return;const R=n.client_id,O=document.getElementById("bank-client-badge-dot"),J=document.getElementById("bank-client-badge-name"),X=document.getElementById("bank-client-badge-caret"),de=typeof _userInfo<"u"?_userInfo:null,se=!(de&&de.role==="member");if(R!=null){const ce=(window._clientsCache||[]).find(ae=>Number(ae.id)===Number(R));v.classList.remove("is-empty"),O&&(O.style.background=ce&&ce.color||"#111111"),J&&(J.textContent=ce&&(ce.short_name||ce.name)||"#"+R)}else v.classList.add("is-empty"),O&&(O.style.background=""),J&&(J.textContent=t("bank-client-none"));se?(v.classList.remove("is-readonly"),v.disabled=!1,X&&(X.style.display="")):(v.classList.add("is-readonly"),v.disabled=!0,X&&(X.style.display="none")),v.style.display=""}let H=null;function E(){if(!n)return;const v=typeof _userInfo<"u"?_userInfo:null;if(!!(v&&v.role==="member"))return;H=n.client_id!=null?Number(n.client_id):null,q();const O=document.getElementById("bank-client-picker-modal");O&&(O.style.display="")}function g(){const v=document.getElementById("bank-client-picker-modal");v&&(v.style.display="none"),H=null}function q(){const v=document.getElementById("bank-client-picker-list");if(!v)return;const R=(window._clientsCache||[]).filter(J=>J&&(J.is_active===!0||J.is_active===void 0)),O=[];O.push('<div class="bank-client-picker-row is-none'+(H==null?" is-selected":"")+'" data-cid=""><span class="bank-cp-dot"></span><span>'+z(t("bank-client-picker-none"))+"</span></div>"),R.forEach(J=>{const X=Number(J.id)===Number(H)?" is-selected":"";O.push('<div class="bank-client-picker-row'+X+'" data-cid="'+z(J.id)+'"><span class="bank-cp-dot" style="background:'+z(J.color||"#111111")+'"></span><span>'+z(J.short_name||J.name||"#"+J.id)+"</span></div>")}),v.innerHTML=O.join(""),v.querySelectorAll(".bank-client-picker-row").forEach(J=>{J.addEventListener("click",()=>{const X=J.dataset.cid;H=X?Number(X):null,q()})})}async function N(){if(n)try{const v=await fetch("/api/bank-recon/sessions/"+encodeURIComponent(n.id)+"/client",{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({client_id:H})});if(!v.ok)throw new Error("client:"+v.status);n.client_id=H,re(),showToast(t("bank-client-changed"),"success"),g();try{await l()}catch{}}catch(v){console.warn("[bank-recon] save client failed",v),showToast(t("bank-client-change-failed"),"error")}}function K(){if(!n)return;const v=n;document.getElementById("bank-detail-title").textContent=(v.bank_code||"-")+(v.account_last4?" ···"+v.account_last4:"")+" · "+(v.source_filename||""),document.getElementById("bank-meta-period").textContent=U(v.period_start,v.period_end)||"-",document.getElementById("bank-meta-opening").textContent=T(v.opening_balance),document.getElementById("bank-meta-inflow").textContent="+"+T(v.total_inflow),document.getElementById("bank-meta-outflow").textContent="-"+T(v.total_outflow),document.getElementById("bank-meta-closing").textContent=T(v.closing_balance);const R=a||[],O=R.length;let J=0,X=0,de=0;for(const se of R){const ce=se.match_status||"unmatched";ce==="matched"?J++:ce==="suggested"?X++:de++}document.getElementById("bank-stat-total").textContent=O,document.getElementById("bank-stat-matched").textContent=J,document.getElementById("bank-stat-suggested").textContent=X,document.getElementById("bank-stat-unmatched").textContent=de}function Z(){const v=document.getElementById("bank-tx-tbody");if(!v)return;let R=a||[];if(o!=="all"&&(R=R.filter(O=>o==="matched"?O.match_status==="matched":o==="suggested"?O.match_status==="suggested":o==="unmatched"?O.match_status==="unmatched"||O.match_status==="ignored":!0)),R.length===0){v.innerHTML=`<tr><td colspan="4" class="bank-empty">${t("bank-tx-empty")}</td></tr>`;return}if(v.innerHTML=R.map(O=>le(O)).join(""),v.querySelectorAll("tr[data-tx-id]").forEach(O=>{O.addEventListener("click",()=>{const J=O.dataset.txId,X=a.find(de=>de.id===J);X&&(v.querySelectorAll("tr.is-selected").forEach(de=>de.classList.remove("is-selected")),O.classList.add("is-selected"),ie(X))})}),s){const O=v.querySelector('tr[data-tx-id="'+s.id+'"]');O&&O.classList.add("is-selected")}}function le(v){const R=v.direction==="OUT",O=R?"-":"+",J=R?"bank-out":"bank-in",X=v.match_status||"unmatched",de=t("bank-match-"+X)||X,se=A(v.tx_date),ce=v.channel?`<span class="bank-tx-channel">${z(v.channel)}</span>`:"";return`
            <tr data-tx-id="${z(v.id)}">
                <td class="bank-tx-date">${z(se)}</td>
                <td class="bank-tx-desc">${ce}${z(v.description||"-")}</td>
                <td class="bank-td-amount ${J}">${O}${T(v.amount)}</td>
                <td><span class="bank-tx-match mt-${X}">${z(de)}</span></td>
            </tr>
        `}async function ie(v){s=v;const R=document.getElementById("bank-detail-body");R&&R.classList.add("has-pane");const O=document.getElementById("bank-cand-pane-title"),J=document.getElementById("bank-cand-pane-sub"),X=document.getElementById("bank-cand-pane-foot");if(O&&(O.textContent=t("bank-cand-pane-current")),J){const se=v.direction==="OUT"?"-":"+",ce=v.direction==="OUT"?"bank-out":"bank-in";J.innerHTML=`${z(A(v.tx_date))}
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <span>${z(v.description||"-")}</span>
                <span style="margin:0 6px;color:#D1D5DB">·</span>
                <strong class="${ce}">${se}${T(v.amount)}</strong>`}X&&(X.style.display="");const de=document.getElementById("bank-cand-pane-body");if(de){de.innerHTML=`<div class="bank-empty">${t("bank-cand-loading")}</div>`;try{const se=await fetch("/api/bank-recon/tx/"+encodeURIComponent(v.id)+"/candidates",{headers:{Authorization:"Bearer "+token}});if(!se.ok)throw new Error("cands:"+se.status);const ce=await se.json();ee(v,ce.candidates||[])}catch{de.innerHTML=`<div class="bank-empty">${t("bank-cand-load-failed")}</div>`}}}function V(v){const R=Number(v||0);let O="score-low";return R>=85?O="score-high":R>=60&&(O="score-mid"),'<span class="bank-cand-score '+O+'">'+R.toFixed(0)+" "+t("bank-cand-score-unit")+"</span>"}function Q(v,R,O){const J=R.history_id,X=R.invoice_no||"-",de=R.vendor||"-",se=R.amount_total!==null&&R.amount_total!==void 0?T(R.amount_total):"-",ce=R.invoice_date?A(R.invoice_date):"-",ae=R.filename||"",pe=!!O&&v.matched_history_id===J,fe="bank-cand-card"+(R.is_auto_picked?" is-auto":"")+(pe?" is-picked":"");let me="";return pe?me='<button class="btn btn-ghost btn-small" data-act="unmatch"><span>'+t("bank-cand-unmatch")+"</span></button>":me='<button class="btn btn-primary btn-small" data-act="pick" data-hid="'+z(J)+'"><span>'+t(R.is_auto_picked?"bank-cand-confirm":"bank-cand-pick-this")+"</span></button>",'<div class="'+fe+'" data-hid="'+z(J)+'"><div class="bank-cand-card-head"><div class="bank-cand-card-vendor">'+z(de)+"</div>"+V(R.score)+'</div><div class="bank-cand-card-fields"><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-invoice-no")+"</span> "+z(X)+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-amount")+"</span> "+se+'</span><span class="bank-cand-field"><span class="bank-cand-flabel">'+t("bank-cand-fld-date")+"</span> "+z(ce)+"</span></div>"+(ae?'<div class="bank-cand-card-file" title="'+z(ae)+'">'+z(ae)+"</div>":"")+(R.reason?'<div class="bank-cand-card-reason">'+z(R.reason)+"</div>":"")+'<div class="bank-cand-card-actions">'+me+"</div></div>"}function ee(v,R){const O=document.getElementById("bank-cand-pane-body");if(!O)return;const J=R||[];let X="";if(v.match_status==="matched")X='<div class="bank-cand-hint hint-matched">'+t("bank-cand-hint-matched").replace("{n}",J.length)+"</div>";else if(v.match_status==="suggested")X='<div class="bank-cand-hint hint-suggested">'+t("bank-cand-hint-suggested").replace("{n}",J.length)+"</div>";else if(J.length>0)X='<div class="bank-cand-hint hint-low">'+t("bank-cand-hint-low").replace("{n}",J.length)+"</div>";else{O.innerHTML='<div class="bank-empty">'+t("bank-cand-no-match-detail")+"</div>";return}const de=v.match_status==="matched",se=J.map(ce=>Q(v,ce,de)).join("");O.innerHTML=X+'<div class="bank-cand-list">'+se+"</div>",O.querySelectorAll('[data-act="pick"]').forEach(ce=>{ce.addEventListener("click",()=>{L(ce.dataset.hid)})}),O.querySelectorAll('[data-act="unmatch"]').forEach(ce=>{ce.addEventListener("click",async()=>{try{await fetch("/api/bank-recon/tx/"+encodeURIComponent(v.id)+"/override",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({status:"unmatched"})}),ne(),await d(n.id)}catch{showToast(t("bank-action-failed"),"error")}})})}function ne(){const v=document.getElementById("bank-detail-body");v&&v.classList.remove("has-pane");const R=document.getElementById("bank-cand-pane-title"),O=document.getElementById("bank-cand-pane-sub"),J=document.getElementById("bank-cand-pane-body"),X=document.getElementById("bank-cand-pane-foot");R&&(R.textContent=t("bank-cand-pane-empty-title")),O&&(O.textContent=t("bank-cand-pane-empty-sub")),X&&(X.style.display="none"),J&&(J.innerHTML='<div class="bank-cand-pane-empty"><svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="14" y="10" width="36" height="44" rx="3"/><path d="M22 22h20M22 30h20M22 38h12"/></svg><div>'+t("bank-cand-pane-empty-hint")+"</div></div>");const de=document.getElementById("bank-tx-tbody");de&&de.querySelectorAll("tr.is-selected").forEach(se=>se.classList.remove("is-selected")),s=null}function oe(v){const R=document.getElementById("bank-upload-progress");R&&(R.style.display="none")}function ue(){const v=document.getElementById("bank-upload-error");v&&(v.style.display="none")}function k(v){return{"bank_recon.only_pdf":t("bank-err-only-pdf"),"bank_recon.empty_file":t("bank-err-empty"),"bank_recon.file_too_large":t("bank-err-too-large"),"bank_recon.save_failed":t("bank-err-server"),"bank_recon.scanned":t("bank-err-scanned"),"bank_recon.no_tx":t("bank-err-no-tx"),network:t("bank-err-network")}[v]||t("bank-err-unknown")+" ("+v+")"}function T(v){if(v==null)return"-";const R=Number(v);return isNaN(R)?"-":R.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function A(v){if(!v)return"-";const R=String(v);return R.length>=10?R.slice(0,10):R}function U(v,R){return!v&&!R?"":(A(v)||"?")+" ~ "+(A(R)||"?")}function z(v){return v==null?"":String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}window._loadBankReconPanel=r,window._rerenderBankRecon=function(){if(currentRoute==="automation"){if(B(),n&&(K(),Z(),re(),!s)){const v=document.getElementById("bank-cand-pane-title"),R=document.getElementById("bank-cand-pane-sub");v&&(v.textContent=t("bank-cand-pane-empty-title")),R&&(R.textContent=t("bank-cand-pane-empty-sub"))}I()}},typeof window.subscribeI18n=="function"&&window.subscribeI18n("bank-recon",window._rerenderBankRecon),window._openBankSession=async function(v){v&&(i||await r(),await d(v))}})();(function(){const e=document.getElementById("page-clients");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e=[],n=null,a="",o="seller";const s={page:0,pageSize:12,keyword:""},i=new Set;let r=[];const u={keyword:""};let l=null;function d(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}async function c(g,q={}){const N=await fetch(g,{...q,headers:{"Content-Type":"application/json",...d(),...q.headers||{}}});if(!N.ok){const K=await N.json().catch(()=>({}));throw new Error(K.detail||"HTTP "+N.status)}return N.json()}async function p(){try{e=(await c("/api/clients")).clients||[],window._clientsCache=e}catch(g){console.error("loadClientsCache fail",g),e=[]}try{typeof window._refreshExcClientFilter=="function"&&window._refreshExcClientFilter()}catch{}try{typeof window._refreshClientSwitcher=="function"&&window._refreshClientSwitcher()}catch{}return e}function f(g){o=g==="buyer"?"buyer":"seller",document.querySelectorAll("[data-cust-tab]").forEach(K=>K.classList.toggle("active",K.dataset.custTab===o));const q=document.getElementById("cust-pane-seller"),N=document.getElementById("cust-pane-buyer");q&&q.classList.toggle("active",o==="seller"),N&&N.classList.toggle("active",o==="buyer")}function m(){const g=window._userInfo||{},q=String(g.role||"").toLowerCase(),N=String(g.tenant_role||"").toLowerCase();return g.is_super_admin===!0||g.is_owner===!0||q==="owner"||q==="admin"||N==="owner"||N==="admin"}function b(){window._workspaceClientsCache=r,typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl()}async function M(){try{const g=await c("/api/workspace/clients");r=g&&(g.clients||g.items)||[],window._workspaceClientsCache=r}catch(g){console.error("loadSellerCache fail",g),r=[]}return r}function I(){const g=u.keyword.trim().toLowerCase();return g?r.filter(q=>(q.name||"").toLowerCase().includes(g)||(q.tax_id||"").toLowerCase().includes(g)):r}function x(){const g=document.getElementById("seller-tbody");if(!g)return;const q=m(),N=document.getElementById("btn-seller-new");N&&(N.style.display=q?"":"none");const K=I(),Z=typeof window.getActiveWorkspaceClientId=="function"?window.getActiveWorkspaceClientId():null;if(!K.length){g.innerHTML=`<div class="cust-empty">${escapeHtml(t(u.keyword?"cust-no-match":"seller-empty"))}</div>`;return}g.innerHTML=K.map(le=>{const V=Z!=null&&Number(Z)===Number(le.id)?`<span class="cust-badge-current"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7.5l3.2 3.2L12 4"/></svg>${escapeHtml(t("seller-current"))}</span>`:`<button class="cust-row-btn primary" data-saction="activate" data-wid="${le.id}">${escapeHtml(t("seller-set-current"))}</button>`,Q=q?`
                <button class="cust-row-btn" data-saction="edit" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2l3 3-7 7H2v-3z"/></svg><span>${escapeHtml(t("client-card-edit"))}</span></button>
                <button class="cust-row-btn danger" data-saction="archive" data-wid="${le.id}"><svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4h10M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4M5.5 4V2.8a1 1 0 011-1h1a1 1 0 011 1V4"/></svg><span>${escapeHtml(t("wsclient-archive"))}</span></button>`:"";return`<div class="cust-row seller-grid" data-wid="${le.id}">
                <div class="cust-cell-name"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:.55"><rect x="2" y="5" width="12" height="9" rx="1"/><path d="M10 14V4a1 1 0 00-1-1H7a1 1 0 00-1 1v10"/></svg><span class="cust-name-text">${escapeHtml(le.name||"#"+le.id)}</span></div>
                <div class="cust-cell-tax">${escapeHtml(le.tax_id||"—")}</div>
                <div class="align-right">${le.invoice_count||0}</div>
                <div class="cust-row-actions">${V}${Q}</div>
            </div>`}).join("")}function y(g){l=g?g.id:null,document.getElementById("wsclient-modal-title").textContent=t(g?"wsclient-modal-edit":"wsclient-modal-new"),document.getElementById("wsclient-input-name").value=g&&g.name||"",document.getElementById("wsclient-input-tax").value=g&&g.tax_id||"",document.getElementById("wsclient-modal-archive").style.display=g?"":"none",document.getElementById("wsclient-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("wsclient-input-name").focus(),50)}function $(){document.getElementById("wsclient-modal-mask").style.display="none",l=null}async function C(){const g=document.getElementById("wsclient-input-name").value.trim(),q=document.getElementById("wsclient-input-tax").value.trim();if(!g){showToast(t("client-msg-name-required"),"fail");return}try{l?(await c("/api/workspace/clients/"+l,{method:"PATCH",body:JSON.stringify({name:g,tax_id:q})}),showToast(t("client-msg-updated"),"success")):(await c("/api/workspace/clients",{method:"POST",body:JSON.stringify({name:g,tax_id:q||null})}),showToast(t("client-msg-created"),"success")),$(),await M(),x(),b()}catch(N){const K=N&&N.message?N.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+K,"fail")}}async function F(){if(!l)return;const g=r.find(N=>Number(N.id)===Number(l));if(await showConfirm(t("wsclient-archive-confirm").replace("{name}",g?g.name:""),{danger:!0}))try{const N=l;await c("/api/workspace/clients/"+N,{method:"DELETE"}),showToast(t("wsclient-archived"),"success"),typeof window.getActiveWorkspaceClientId=="function"&&Number(window.getActiveWorkspaceClientId())===Number(N)&&typeof window.enterPersonalMode=="function"&&window.enterPersonalMode(),$(),await M(),x(),b()}catch{showToast(t("client-msg-save-fail"),"fail")}}function j(){const g=s.keyword.trim().toLowerCase();return g?e.filter(q=>(q.name||"").toLowerCase().includes(g)||(q.short_name||"").toLowerCase().includes(g)||(q.tax_id||"").toLowerCase().includes(g)):e}function _(){const g=j(),q=s.pageSize,N=Math.max(0,Math.ceil(g.length/q)-1);s.page>N&&(s.page=N);const K=s.page*q;return{all:g,items:g.slice(K,K+q),start:K,ps:q,total:g.length,maxPage:N}}function h(){const g=document.getElementById("buyer-tbody");if(!g)return;const{items:q,start:N,ps:K,total:Z,maxPage:le}=_();Z?g.innerHTML=q.map(ee=>{const ne=i.has(ee.id);return`<div class="cust-row buyer-grid${ne?" selected":""}" data-cid="${ee.id}">
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
                </div>`}).join(""):g.innerHTML=`<div class="cust-empty">${escapeHtml(t(s.keyword?"cust-no-match":"clients-empty"))}</div>`;const ie=document.getElementById("buyer-pager-info");ie&&(ie.textContent=Z?`${N+1}–${Math.min(N+K,Z)} / ${Z}`:"0");const V=document.getElementById("buyer-prev");V&&(V.disabled=s.page<=0);const Q=document.getElementById("buyer-next");Q&&(Q.disabled=s.page>=le),w()}function w(){const g=i.size,q=document.getElementById("buyer-batch-bar");q&&(q.style.display=g?"flex":"none");const N=document.getElementById("buyer-batch-count");N&&(N.textContent=t("cust-selected-n").replace("{n}",g));const K=document.getElementById("buyer-check-all");if(K){const{items:Z}=_(),le=Z.map(V=>V.id),ie=le.filter(V=>i.has(V)).length;K.checked=le.length>0&&ie===le.length,K.indeterminate=ie>0&&ie<le.length}}function L(){i.clear(),h()}async function S(){const g=Array.from(i);if(!(!g.length||!await showConfirm(t("cust-batch-del-confirm").replace("{n}",g.length),{danger:!0})))try{await c("/api/clients/batch-delete",{method:"POST",body:JSON.stringify({ids:g})}),showToast(t("client-msg-deleted"),"success"),i.clear(),await p(),h(),te(),E()}catch{showToast(t("client-msg-save-fail"),"fail")}}window.loadClientsPage=async function(){const g=document.getElementById("seller-tbody");g&&(g.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`);const q=document.getElementById("buyer-tbody");q&&(q.innerHTML=`<div class="cust-loading">${escapeHtml(t("clients-loading"))}</div>`),await Promise.all([M(),p()]),x(),h()},window.addEventListener("pearnly:workspace-changed",function(){typeof currentRoute<"u"&&currentRoute==="clients"&&x()});function D(g){n=g?g.id:null;const q=!!g;document.getElementById("client-modal-title").textContent=t(q?"client-modal-edit":"client-modal-new"),document.getElementById("client-input-name").value=g&&g.name||"",document.getElementById("client-input-short").value=g&&g.short_name||"",document.getElementById("client-input-tax").value=g&&g.tax_id||"",document.getElementById("client-input-address").value=g&&g.address||"",document.getElementById("client-input-contact").value=g&&g.contact_person||"",document.getElementById("client-input-phone").value=g&&g.contact_phone||"",document.getElementById("client-input-email").value=g&&g.contact_email||"",document.getElementById("client-input-notes").value=g&&g.notes||"";const N=g&&g.color||"#111111";document.querySelectorAll("#client-color-picker .color-swatch").forEach(K=>{K.classList.toggle("active",K.dataset.color===N)}),document.getElementById("client-modal-delete").style.display=q?"":"none",document.getElementById("client-modal-mask").style.display="flex",setTimeout(()=>document.getElementById("client-input-name").focus(),50)}function B(){document.getElementById("client-modal-mask").style.display="none",n=null}function P(){const g=document.querySelector("#client-color-picker .color-swatch.active");return g?g.dataset.color:"#111111"}async function Y(){const g=document.getElementById("client-input-name").value.trim();if(!g){showToast(t("client-msg-name-required"),"fail");return}const q={name:g,short_name:document.getElementById("client-input-short").value.trim()||null,tax_id:document.getElementById("client-input-tax").value.trim()||null,address:document.getElementById("client-input-address").value.trim()||null,contact_person:document.getElementById("client-input-contact").value.trim()||null,contact_phone:document.getElementById("client-input-phone").value.trim()||null,contact_email:document.getElementById("client-input-email").value.trim()||null,notes:document.getElementById("client-input-notes").value.trim()||null,color:P()};try{n?(await c(`/api/clients/${n}`,{method:"PATCH",body:JSON.stringify(q)}),showToast(t("client-msg-updated"),"success")):(await c("/api/clients",{method:"POST",body:JSON.stringify(q)}),showToast(t("client-msg-created"),"success")),B(),await p(),currentRoute==="clients"&&h(),te(),E()}catch(N){console.error("saveClient fail",N);const K=N&&N.message?N.message:t("client-msg-save-fail");showToast(t("client-msg-save-fail")+" · "+K,"fail")}}async function G(){if(!n)return;const g=e.find(K=>K.id===n);if(!g)return;const q=t("client-delete-confirm").replace("{name}",g.name);if(await showConfirm(q,{danger:!0}))try{await c(`/api/clients/${n}`,{method:"DELETE"}),showToast(t("client-msg-deleted"),"success"),B(),await p(),currentRoute==="clients"&&h(),te(),E()}catch(K){console.error(K),showToast(t("client-msg-save-fail"),"fail")}}async function W(g){const q=e.find(N=>N.id===g);if(typeof window.openClientExportModal=="function"){window.openClientExportModal(g,q?q.name:"");return}try{const N=localStorage.getItem("mrpilot_token"),K=await fetch(`/api/clients/${g}/export?month=all`,{headers:{Authorization:"Bearer "+N}});if(!K.ok){let Q="HTTP "+K.status;try{const ee=await K.json();ee&&ee.detail&&(Q=ee.detail)}catch{}throw new Error(Q)}const Z=await K.blob();if(Z.size<200){showToast(t("client-export-month-empty"),"info");return}const le=q&&q.name?q.name.replace(/[^a-zA-Z0-9\u0e00-\u0e7f\u4e00-\u9fff]/g,"_").slice(0,40):"client",ie=URL.createObjectURL(Z),V=document.createElement("a");V.href=ie,V.download=`${le}_export.csv`,V.click(),URL.revokeObjectURL(ie)}catch(N){console.error("exportClient fail",N),showToast(t("client-msg-save-fail")+" · "+(N.message||""),"fail")}}function te(){const g=document.getElementById("drawer-client-select");if(!g)return;const q=g.value;g.innerHTML=`<option value="">${escapeHtml(t("drawer-client-none"))}</option>`+e.map(N=>`<option value="${N.id}">${escapeHtml(N.name)}</option>`).join(""),g.value=q||""}window.bindDrawerClient=function(g,q){const N=document.getElementById("drawer-client-select");if(!N)return;if(te(),N.value=q?String(q):"",!g){N.onchange=null;const Z=document.getElementById("drawer-client-add");Z&&(Z.onclick=()=>D(null));return}N.onchange=async()=>{const Z=N.value?parseInt(N.value,10):null;try{await c(`/api/history/${g}/assign_client`,{method:"POST",body:JSON.stringify({client_id:Z})}),showToast(t("client-msg-updated"),"success");const le=_results[_drawerIdx];le&&(le.client_id=Z),await p()}catch(le){console.error(le),showToast(t("client-msg-save-fail"),"fail"),N.value=q?String(q):""}};const K=document.getElementById("drawer-client-add");K&&(K.onclick=()=>D(null))};let re={fetched:0,items:[],supplier_count:0};window.fillCategoryDatalist=async function(){try{const g=document.getElementById("drawer-cat-datalist"),q=Date.now();if(q-re.fetched<300*1e3){g&&(g.innerHTML=re.items.map(K=>`<option value="${escapeHtml(K)}">`).join("")),H(re.supplier_count);return}const N=await c("/api/categories",{method:"GET"});re.fetched=q,re.items=N&&N.categories||[],re.supplier_count=N&&N.supplier_count||0,g&&(g.innerHTML=re.items.map(K=>`<option value="${escapeHtml(K)}">`).join("")),H(re.supplier_count)}catch(g){console.warn("fillCategoryDatalist failed",g)}};function H(g){const q=document.getElementById("drawer-cat-learned-tag");q&&g>0&&(q.textContent=(t("drawer-suggest-learned-with-count")||"已学 {n}").replace("{n}",g))}function E(){const g=document.getElementById("history-client-filter");if(!g)return;const q=g.value;g.innerHTML=`<option value="">${escapeHtml(t("history-client-all"))}</option>`+e.map(N=>`<option value="${N.id}">${escapeHtml(N.name)}</option>`).join(""),g.value=q||""}window.getHistoryClientFilter=function(){return a},document.addEventListener("DOMContentLoaded",()=>{const g=document.querySelector(".cust-tab-bar");g&&g.addEventListener("click",ae=>{const pe=ae.target.closest("[data-cust-tab]");pe&&f(pe.dataset.custTab)});const q=document.getElementById("btn-buyer-new");q&&q.addEventListener("click",()=>D(null));const N=document.getElementById("buyer-tbody");N&&N.addEventListener("click",ae=>{const pe=ae.target.closest(".buyer-row-check");if(pe){const ge=parseInt(pe.dataset.cid,10);pe.checked?i.add(ge):i.delete(ge);const ye=pe.closest(".cust-row");ye&&ye.classList.toggle("selected",pe.checked),w();return}const fe=ae.target.closest(".cust-row-btn");if(fe){ae.stopPropagation();const ge=parseInt(fe.dataset.cid,10);if(fe.dataset.action==="edit"){const ye=e.find(xe=>xe.id===ge);ye&&D(ye)}else fe.dataset.action==="export"&&W(ge);return}const me=ae.target.closest(".cust-row");if(me&&!ae.target.closest(".cust-cell-check")){const ge=e.find(ye=>ye.id===parseInt(me.dataset.cid,10));ge&&D(ge)}});const K=document.getElementById("buyer-check-all");K&&K.addEventListener("change",()=>{const{items:ae}=_();ae.forEach(pe=>{K.checked?i.add(pe.id):i.delete(pe.id)}),h()});const Z=document.getElementById("buyer-batch-cancel");Z&&Z.addEventListener("click",L);const le=document.getElementById("buyer-batch-delete");le&&le.addEventListener("click",S);const ie=document.getElementById("buyer-prev");ie&&ie.addEventListener("click",()=>{s.page>0&&(s.page--,h())});const V=document.getElementById("buyer-next");V&&V.addEventListener("click",()=>{s.page++,h()});const Q=document.getElementById("buyer-search");if(Q){let ae;Q.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{s.keyword=Q.value,s.page=0;const pe=document.getElementById("buyer-search-clear");pe&&(pe.style.display=Q.value?"":"none"),h()},200)})}const ee=document.getElementById("buyer-search-clear");ee&&ee.addEventListener("click",()=>{const ae=document.getElementById("buyer-search");ae&&(ae.value=""),s.keyword="",s.page=0,ee.style.display="none",h()});const ne=document.getElementById("btn-seller-new");ne&&ne.addEventListener("click",()=>y(null));const oe=document.getElementById("seller-tbody");oe&&oe.addEventListener("click",ae=>{const pe=ae.target.closest("[data-saction]");if(!pe)return;ae.stopPropagation();const fe=parseInt(pe.dataset.wid,10),me=pe.dataset.saction,ge=r.find(ye=>Number(ye.id)===fe);me==="activate"?(typeof window.setActiveWorkspaceClientId=="function"&&window.setActiveWorkspaceClientId(fe),x(),typeof window.renderWorkspaceControl=="function"&&window.renderWorkspaceControl(),showToast(t("seller-activated").replace("{name}",ge?ge.name:""),"success")):me==="edit"?ge&&y(ge):me==="archive"&&(l=fe,F())});const ue=document.getElementById("seller-search");if(ue){let ae;ue.addEventListener("input",()=>{clearTimeout(ae),ae=setTimeout(()=>{u.keyword=ue.value;const pe=document.getElementById("seller-search-clear");pe&&(pe.style.display=ue.value?"":"none"),x()},200)})}const k=document.getElementById("seller-search-clear");k&&k.addEventListener("click",()=>{const ae=document.getElementById("seller-search");ae&&(ae.value=""),u.keyword="",k.style.display="none",x()});const T=document.getElementById("wsclient-modal-close");T&&T.addEventListener("click",$);const A=document.getElementById("wsclient-modal-cancel");A&&A.addEventListener("click",$);const U=document.getElementById("wsclient-modal-save");U&&U.addEventListener("click",C);const z=document.getElementById("wsclient-modal-archive");z&&z.addEventListener("click",F);const v=document.getElementById("wsclient-modal-mask");v&&v.addEventListener("click",ae=>{ae.target===v&&$()});const R=document.getElementById("client-modal-close");R&&R.addEventListener("click",B);const O=document.getElementById("client-modal-cancel");O&&O.addEventListener("click",B);const J=document.getElementById("client-modal-save");J&&J.addEventListener("click",Y);const X=document.getElementById("client-modal-delete");X&&X.addEventListener("click",G);const de=document.getElementById("client-modal-mask");de&&de.addEventListener("click",ae=>{ae.target===de&&B()});const se=document.getElementById("client-color-picker");se&&se.addEventListener("click",ae=>{const pe=ae.target.closest(".color-swatch");pe&&(se.querySelectorAll(".color-swatch").forEach(fe=>fe.classList.remove("active")),pe.classList.add("active"))});const ce=document.getElementById("history-client-filter");ce&&ce.addEventListener("change",()=>{a=ce.value,typeof renderHistoryList=="function"&&renderHistoryList()})}),setTimeout(()=>p(),1e3)})();(function(){const e=document.getElementById("page-exceptions");if(!(!e||e.dataset.wbInjected==="1")){e.innerHTML=`
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
`,e.dataset.wbInjected="1";try{const n=window._currentLang||localStorage.getItem("mrpilot_lang")||"th",a=window.I18N;a&&a[n]&&(e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[n][s]&&(o.textContent=a[n][s])}),e.querySelectorAll("[data-i18n-placeholder]").forEach(o=>{const s=o.getAttribute("data-i18n-placeholder");a[n][s]&&(o.placeholder=a[n][s])}))}catch{}}})();(function(){let e={statsCache:null,listCache:[],currentRule:null,currentClient:"",currentStatus:"pending",loading:!1,selectedIds:new Set,offset:0,pageSize:50,total:0,loadFailed:!1,listScrollY:0};function n(H,E){let g=t(H)||H;if(E)for(const q in E)g=g.replace(new RegExp("\\{"+q+"\\}","g"),String(E[q]));return g}async function a(){try{const H=e.currentClient||"",E="/api/exceptions/stats?status=pending"+(H?"&client_id="+encodeURIComponent(H):""),g=await fetch(E,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!g.ok)return;const q=await g.json(),N=document.getElementById("nav-exc-badge");if(!N)return;const K=parseInt(q.pending||0,10);K>0?(N.textContent=K>99?"99+":String(K),N.style.display=""):N.style.display="none"}catch{}}function o(H){return H==="high"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 1.5L1 12.5h12L7 1.5z"/>
                <line x1="7" y1="6" x2="7" y2="9"/>
                <circle cx="7" cy="10.6" r="0.5" fill="currentColor"/>
            </svg>`:H==="medium"?`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="7" cy="7" r="5.5"/>
                <line x1="7" y1="4" x2="7" y2="7.5"/>
                <circle cx="7" cy="9.5" r="0.5" fill="currentColor"/>
            </svg>`:`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="7" cy="7" r="5.5"/>
            <line x1="4.5" y1="7" x2="9.5" y2="7"/>
        </svg>`}function s(){return`<svg class="exc-empty-icon" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 19l5 5 13-13"/>
            <circle cx="20" cy="20" r="17"/>
        </svg>`}function i(H){if(H==null)return"—";const E=parseFloat(H);return isNaN(E)?"—":"฿ "+E.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function r(H){return H?H.slice(0,10):"—"}function u(H){document.getElementById("exc-kpi-pending").textContent=H.pending||0,document.getElementById("exc-kpi-high").textContent=H.high_severity||0,document.getElementById("exc-kpi-resolved").textContent=H.resolved||0,document.getElementById("exc-kpi-learned").textContent=H.learned_rules||0;const E=document.getElementById("exc-status-tab-count-pending"),g=document.getElementById("exc-status-tab-count-resolved"),q=document.getElementById("exc-status-tab-count-ignored");E&&(E.textContent=H.pending||0),g&&(g.textContent=H.resolved||0),q&&(q.textContent=H.ignored||0),document.querySelectorAll("#exc-status-tabs .exc-status-tab").forEach(K=>{K.classList.toggle("active",K.dataset.status===(e.currentStatus||"pending"))})}function l(H){const E=document.getElementById("exc-chips");if(!E)return;const g=H.by_rule||{},q=["confidence_low","duplicate","amount_missing","math_mismatch","tax_id_format_invalid"];let K=`<button class="exc-chip ${!e.currentRule?"active":""}" data-rule="">
            <span>${escapeHtml(t("exc-chip-all"))}</span>
            <span class="exc-chip-count">${H.pending||0}</span>
        </button>`;for(const Z of q){const le=g[Z]||0;if(le===0&&e.currentRule!==Z)continue;const ie=e.currentRule===Z;K+=`<button class="exc-chip ${ie?"active":""}" data-rule="${escapeHtml(Z)}">
                <span>${escapeHtml(t("exc-chip-"+Z))}</span>
                <span class="exc-chip-count">${le}</span>
            </button>`}E.innerHTML=K,E.querySelectorAll(".exc-chip").forEach(Z=>{Z.addEventListener("click",()=>{const le=Z.dataset.rule||null;e.currentRule=le,b()})})}function d(H){const E=document.getElementById("exc-list");if(!E)return;if(!H||H.length===0){E.innerHTML=`<div class="exc-empty">
                ${s()}
                <div class="exc-empty-title">${escapeHtml(t("exc-empty-title"))}</div>
                <div>${escapeHtml(t("exc-empty-desc"))}</div>
            </div>`,p();return}const g='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7l3 3 5-5"/></svg>',q=(e.currentStatus||"pending")==="pending";E.innerHTML=H.map(N=>{const K=N.severity||"medium",Z=t("exc-rule-"+N.rule_code)||N.rule_code,le=N.seller_name&&N.seller_name.trim()?N.seller_name:t("exc-no-seller"),ie=N.filename||"—",V=r(N.invoice_date||N.created_at),Q=N.status==="pending",ee=e.selectedIds.has(N.id),ne=q&&Q;return`
                <div class="exc-row sev-${escapeHtml(K)} ${ee?"selected":""}" data-exc-id="${escapeHtml(String(N.id))}">
                    <div class="exc-row-check ${ee?"checked":""}" data-check-id="${escapeHtml(String(N.id))}" ${ne?"":'style="visibility:hidden;"'}>${g}</div>
                    <div class="exc-row-sev">${o(K)}</div>
                    <div class="exc-row-main">
                        <div class="exc-row-title">${escapeHtml(le)} · ${escapeHtml(ie)}</div>
                        <div class="exc-row-meta">
                            ${N.invoice_no?`<span><b>${escapeHtml(N.invoice_no)}</b></span>`:""}
                            <span>${escapeHtml(V)}</span>
                        </div>
                    </div>
                    <div class="exc-row-rule r-${escapeHtml(K)}">${escapeHtml(Z)}</div>
                    <div class="exc-row-amount">${escapeHtml(i(N.total_amount))}</div>
                </div>
            `}).join(""),E.querySelectorAll(".exc-row").forEach(N=>{N.addEventListener("click",K=>{if(K.target.closest(".exc-row-check"))return;const Z=N.dataset.excId;Z&&C(parseInt(Z,10))})}),E.querySelectorAll(".exc-row-check").forEach(N=>{N.addEventListener("click",K=>{K.stopPropagation();const Z=parseInt(N.dataset.checkId,10);Z&&(e.selectedIds.has(Z)?(e.selectedIds.delete(Z),N.classList.remove("checked"),N.closest(".exc-row").classList.remove("selected")):(e.selectedIds.add(Z),N.classList.add("checked"),N.closest(".exc-row").classList.add("selected")),c())})}),c(),p()}function c(){const H=document.getElementById("exc-batch-bar"),E=document.getElementById("exc-batch-count");if(!H||!E)return;const g=e.selectedIds.size;g===0?H.style.display="none":(H.style.display="",E.textContent=n("exc-batch-count",{n:g}))}function p(){const H=document.getElementById("exc-list-foot"),E=document.getElementById("exc-list-count"),g=document.getElementById("exc-loadmore");if(!H||!E||!g)return;const q=e.listCache.length;if(q===0){H.style.display="none";return}H.style.display="";let N=q;const K=e.statsCache;K&&(e.currentRule?N=(K.by_rule||{})[e.currentRule]||q:N=K.pending||q),e.total=N,E.textContent=n("exc-list-count",{shown:q,total:N});const Z=q<N&&q<500;g.style.display=Z?"":"none"}async function f(){try{if(navigator.onLine===!1)throw new Error("offline");const H=e.currentClient||"",E=e.currentStatus||"pending",g=new URLSearchParams;g.set("status",E),H&&g.set("client_id",H);const q="/api/exceptions/stats?"+g.toString(),N=await fetch(q,{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!N.ok)throw new Error("http "+N.status);const K=await N.json();return e.statsCache=K,u(K),l(K),K}catch(H){return console.warn("loadExceptionsStats fail",H),null}}function m(H){const E=document.getElementById("exc-list");if(!E)return;const g=`<svg class="exc-error-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="18" r="14"/>
            <line x1="18" y1="11" x2="18" y2="19"/>
            <circle cx="18" cy="23" r="0.8" fill="currentColor"/>
        </svg>`,q=H?t("exc-offline"):t("exc-error-retry-title"),N=H?"":t("exc-error-retry-desc");E.innerHTML=`
            <div class="exc-error">
                ${g}
                <div class="exc-error-msg">${escapeHtml(q)}${N?" · "+escapeHtml(N):""}</div>
                <button class="btn btn-sm btn-secondary" id="exc-retry-btn" type="button">${escapeHtml(t("exc-retry-btn"))}</button>
            </div>`;const K=document.getElementById("exc-retry-btn");K&&K.addEventListener("click",()=>window.loadExceptionsPage&&window.loadExceptionsPage())}async function b(H){H=H||{};const E=!!H.append,g=document.getElementById("exc-list");!E&&g&&e.listCache.length===0&&(g.innerHTML=`<div class="exc-loading">${escapeHtml(t("exc-loading"))}</div>`);const q=new URLSearchParams;q.set("status",e.currentStatus||"pending"),e.currentRule&&q.set("rule_code",e.currentRule),e.currentClient&&q.set("client_id",e.currentClient);const N=E?e.listCache.length:0;q.set("limit",String(e.pageSize)),q.set("offset",String(N));try{if(navigator.onLine===!1)throw new Error("offline");const K=await fetch("/api/exceptions/list?"+q.toString(),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!K.ok)throw new Error("http "+K.status);const le=(await K.json()).items||[];E?e.listCache=e.listCache.concat(le):(e.listCache=le,e.selectedIds.clear()),e.loadFailed=!1,d(e.listCache),e.statsCache&&l(e.statsCache)}catch(K){console.warn("loadExceptionsList fail",K),e.loadFailed=!0;const Z=navigator.onLine===!1||String(K.message||"").includes("offline");E?showToast(t("exc-toast-load-fail"),"error"):(m(Z),showToast(Z?t("exc-offline"):t("exc-toast-load-fail"),"error"))}}async function M(){if(!e.loading&&!(e.listCache.length>=500)){e.loading=!0;try{await b({append:!0})}finally{e.loading=!1}}}function I(){const H=document.getElementById("exc-client-filter");if(!H)return;const E=window._clientsCache||[],g=e.currentClient||"",q=typeof t=="function"?t("history-client-all"):"全部客户";H.innerHTML=`<option value="">${escapeHtml(q)}</option>`+E.map(N=>`<option value="${N.id}">${escapeHtml(N.name)}</option>`).join(""),H.value=g}window.loadExceptionsPage=async function(){if(!e.loading){e.loading=!0;try{I(),typeof window.loadErpExceptions=="function"&&window.loadErpExceptions(),await f(),await b()}finally{e.loading=!1}}},window.refreshExcBadge=a,window._refreshExcClientFilter=I,window._excState=e,window._rerenderExceptions=function(){try{I()}catch{}e.statsCache&&(u(e.statsCache),l(e.statsCache)),e.listCache&&e.listCache.length&&d(e.listCache);try{window._erpExcState&&window._erpExcState.items&&window._erpExcState.items.length&&typeof window._rerenderErpExceptions=="function"&&window._rerenderErpExceptions()}catch{}x.openExcId&&L()};let x={openExcId:null,excRow:null,history:null,loading:!1,pdfUrl:null,pdfStatus:"idle",editing:!1,editFields:null};function y(){if(x.pdfUrl){try{URL.revokeObjectURL(x.pdfUrl)}catch{}x.pdfUrl=null}x.pdfStatus="idle"}async function $(H,E){x.pdfStatus="loading",L();try{const g=await fetch("/api/history/"+encodeURIComponent(H)+"/pdf",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(x.openExcId!==E)return;if(g.status===404){x.pdfStatus="empty",L();return}if(!g.ok)throw new Error("http "+g.status);const q=await g.blob();if(x.openExcId!==E)return;y(),x.pdfUrl=URL.createObjectURL(q),x.pdfStatus="ready",L()}catch(g){if(x.openExcId!==E)return;console.warn("loadDrawerPdf fail",g),x.pdfStatus="error",L()}}function C(H){const E=(e.listCache||[]).find(g=>g.id===H);if(!E){showToast(t("exc-drawer-error"),"error");return}e.listScrollY=window.scrollY||document.documentElement.scrollTop||0,y(),x.editing=!1,x.editFields=null,x.openExcId=H,x.excRow=E,x.history=null,document.getElementById("exc-drawer-mask").classList.add("show"),document.getElementById("exc-drawer").classList.add("show"),L(),j(E.history_id),$(E.history_id,H)}function F(){y(),x.editing=!1,x.editFields=null,x.openExcId=null,x.excRow=null,x.history=null,document.getElementById("exc-drawer-mask").classList.remove("show"),document.getElementById("exc-drawer").classList.remove("show");const H=e.listScrollY||0;H>0&&requestAnimationFrame(()=>window.scrollTo(0,H))}async function j(H){try{const E=await fetch("/api/history/"+encodeURIComponent(H),{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!E.ok)throw new Error("http "+E.status);x.history=await E.json()}catch(E){console.warn("loadHistoryDetail fail",E),x.history={_err:!0}}x.excRow&&L()}function _(H){if(!H||!H.pages)return{};const E=H.pages,g=E.find(q=>!q.is_duplicate&&!q.is_copy)||E[0];return g&&g.fields||{}}function h(H){if(H==null)return"—";const E=typeof H=="number"?H:parseFloat(String(H).replace(/,/g,""));return isNaN(E)?escapeHtml(String(H)):"฿ "+E.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2})}function w(H,E){if(E=E||{},H==="math_mismatch")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-subtotal"))}</b><span>${escapeHtml(h(E.subtotal))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-vat"))}</b><span>${escapeHtml(h(E.vat))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(h(E.total_expected))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-actual"))}</b><span class="v-bad">${escapeHtml(h(E.total_actual))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-diff"))}</b><span class="v-bad">${escapeHtml(h(E.diff))}</span></div>
            `;if(H==="tax_id_format_invalid")return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-seller-tax"))}</b><span class="v-bad">${escapeHtml(E.tax_id_normalized||E.tax_id_raw||"—")}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-tax-len"))}</b><span class="v-bad">${escapeHtml(String(E.actual_length||"?"))}</span></div>
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span class="v-good">${escapeHtml(t("exc-detail-tax-expected"))}</span></div>
            `;if(H==="duplicate"){const g=E.level==="exact"?t("exc-detail-dup-level-exact"):t("exc-detail-dup-level-likely");return`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-dup-match"))}</b><span>${escapeHtml(E.match_filename||"—")}</span></div>
                ${E.match_invoice_no?`<div class="exc-why-detail-row"><b>${escapeHtml(t("exc-fld-invoice-no"))}</b><span>${escapeHtml(E.match_invoice_no)}</span></div>`:""}
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-expected"))}</b><span>${escapeHtml(g)}</span></div>
            `}return H==="confidence_low"?`
                <div class="exc-why-detail-row"><b>${escapeHtml(t("exc-detail-conf-label"))}</b><span class="v-bad">${escapeHtml(E.confidence||"—")}</span></div>
            `:H==="amount_missing"?`<div class="exc-why-detail-row" style="justify-content:center;color:var(--danger);"><span>${escapeHtml(t("exc-detail-missing"))}</span></div>`:`<div class="exc-why-detail-row"><span style="font-size:11px;">${escapeHtml(JSON.stringify(E))}</span></div>`}function L(){const H=x.excRow;if(!H)return;const E=H.seller_name&&H.seller_name.trim()?H.seller_name:t("exc-no-seller"),g=H.filename||"—";document.getElementById("exc-drawer-title").textContent=g;const q="exc-status-"+(H.status||"pending"),N=t(q)||H.status,K="s-"+(H.status||"pending"),Z=(H.invoice_date||H.created_at||"").slice(0,10);document.getElementById("exc-drawer-sub").innerHTML=`
            <span>${escapeHtml(E)}</span>
            ${H.invoice_no?`<span>· ${escapeHtml(H.invoice_no)}</span>`:""}
            ${Z?`<span>· ${escapeHtml(Z)}</span>`:""}
            <span class="exc-status-chip ${K}">${escapeHtml(N)}</span>
        `;const le=H.severity||"medium",ie=t("exc-rule-"+H.rule_code)||H.rule_code,V=w(H.rule_code,H.detail||{}),Q=_(x.history),ee=x.history===null,ne=x.history&&x.history._err,oe=new Set;H.rule_code==="math_mismatch"?(oe.add("subtotal"),oe.add("vat"),oe.add("total_amount")):H.rule_code==="tax_id_format_invalid"?oe.add("seller_tax"):H.rule_code==="amount_missing"&&(oe.add("total_amount"),oe.add("invoice_number"));const ue=!!x.editing,k=x.editFields||{},T=(ae,pe,fe)=>{if(ee)return`<div class="exc-field-row"><label>${escapeHtml(t(pe))}</label><span class="val empty">…</span></div>`;const me=ue?k[ae]!==void 0?k[ae]:Q[ae]!==void 0&&Q[ae]!==null?Q[ae]:"":Q[ae],ge=oe.has(ae)?"flagged":"";if(ue){const ze=fe?"number":"text",Te=fe?' step="0.01" inputmode="decimal"':"",He=me==null?"":String(me).replace(/"/g,"&quot;");return`<div class="exc-field-row ${ge} editing">
                    <label>${escapeHtml(t(pe))}</label>
                    <input class="exc-field-input" type="${ze}"${Te} data-edit-key="${escapeHtml(ae)}" value="${He}">
                </div>`}const ye=fe?h(me):me||"",xe=me==null||me===""?`<span class="val empty">${escapeHtml(t("exc-empty-val"))}</span>`:`<span class="val">${escapeHtml(ye)}</span>`;return`<div class="exc-field-row ${ge}"><label>${escapeHtml(t(pe))}</label>${xe}</div>`};let A="";ne?A=`<div class="exc-drawer-error">${escapeHtml(t("exc-drawer-error"))}</div>`:A=`
                <div class="exc-fields">
                    ${T("invoice_number","exc-fld-invoice-no",!1)}
                    ${T("date","exc-fld-date",!1)}
                    ${T("seller_name","exc-fld-seller",!1)}
                    ${T("seller_tax","exc-fld-seller-tax",!1)}
                    ${T("buyer_name","exc-fld-buyer",!1)}
                    ${T("buyer_tax","exc-fld-buyer-tax",!1)}
                    ${T("subtotal","exc-fld-subtotal",!0)}
                    ${T("vat","exc-fld-vat",!0)}
                    ${T("total_amount","exc-fld-total",!0)}
                </div>
            `;const U=(()=>{if(x.pdfStatus==="loading"||x.pdfStatus==="idle")return`
                    <div class="exc-pdf-toolbar">
                        <span class="exc-pdf-toolbar-title">${escapeHtml(t("exc-pdf-loading"))}</span>
                    </div>
                    <div class="exc-pdf-empty">
                        <svg class="exc-pdf-empty-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M18 4v8a14 14 0 1014 14"/>
                        </svg>
                        <div class="exc-pdf-empty-msg">${escapeHtml(t("exc-pdf-loading"))}</div>
                    </div>
                `;if(x.pdfStatus==="empty")return`
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
                `;if(x.pdfStatus==="error")return`
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
                `;const ae=x.pdfUrl;return`
                <div class="exc-pdf-toolbar">
                    <span class="exc-pdf-toolbar-title">${escapeHtml(g)}</span>
                    <div class="exc-pdf-toolbar-actions">
                        <a class="exc-pdf-icon-btn" id="exc-pdf-open-tab" href="${ae}" target="_blank" rel="noopener" title="${escapeHtml(t("exc-pdf-open-tab"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M8 2h4v4M12 2L7 7"/>
                                <path d="M11 8v3a1 1 0 01-1 1H3a1 1 0 01-1-1V4a1 1 0 011-1h3"/>
                            </svg>
                        </a>
                        <a class="exc-pdf-icon-btn" id="exc-pdf-download" href="${ae}" download="${escapeHtml(g)}" title="${escapeHtml(t("exc-pdf-download"))}">
                            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M7 2v8M3.5 6.5L7 10l3.5-3.5M2 12h10"/>
                            </svg>
                        </a>
                    </div>
                </div>
                <iframe class="exc-pdf-frame" src="${ae}#toolbar=0&navpanes=0" title="PDF preview"></iframe>
            `})();document.getElementById("exc-drawer-body").innerHTML=`
            <div class="exc-pdf-pane">${U}</div>
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
                        <div class="exc-why-detail">${V}</div>
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
                        ${H.status==="pending"&&!ee&&!ne?ue?`
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
                    ${A}
                </div>
            </div>
        `;const z=document.getElementById("exc-fld-edit");z&&z.addEventListener("click",()=>{x.editing=!0,x.editFields={..._(x.history)},L()});const v=document.getElementById("exc-fld-cancel");v&&v.addEventListener("click",()=>{x.editing=!1,x.editFields=null,L()});const R=document.getElementById("exc-fld-save");R&&R.addEventListener("click",()=>S()),document.querySelectorAll(".exc-field-input").forEach(ae=>{ae.addEventListener("input",()=>{x.editFields||(x.editFields={}),x.editFields[ae.dataset.editKey]=ae.value})});const J=document.getElementById("exc-pdf-retry");J&&x.openExcId&&J.addEventListener("click",()=>{x.excRow&&$(x.excRow.history_id,x.openExcId)});const X=H.status==="pending",de=!!(H.seller_name&&H.seller_name.trim()),se=document.getElementById("exc-btn-resolve"),ce=document.getElementById("exc-btn-ignore");se.disabled=!X,ce.disabled=!X||!de,ce.title=de?t("exc-ignore-hint"):t("exc-ignore-no-seller")}async function S(){if(!x.openExcId||!x.history||!x.history.pages||x.loading)return;x.loading=!0;const H=showToast(t("exc-fld-saving"),"loading",0);try{const E=JSON.parse(JSON.stringify(x.history.pages||[]));let g=E.findIndex(ie=>!ie.is_duplicate&&!ie.is_copy);g<0&&(g=0),E[g]||(E[g]={fields:{}});const q=E[g].fields||{},N=x.editFields||{},K=new Set(["subtotal","vat","total_amount"]),Z={...q};for(const ie in N){let V=N[ie];if((V===""||V===void 0)&&(V=null),K.has(ie)&&V!==null){const Q=parseFloat(V);V=isNaN(Q)?null:Q}Z[ie]=V}E[g].fields=Z;const le=await fetch("/api/history/"+encodeURIComponent(x.history.id),{method:"PUT",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({pages:E})});if(!le.ok)throw new Error("http "+le.status);H(),showToast(t("exc-fld-save-ok"),"success"),F(),await f(),await b(),a()}catch(E){H(),console.warn("save fields fail",E),showToast(t("exc-fld-save-fail"),"error")}finally{x.loading=!1}}async function D(){if(!(!x.openExcId||x.loading)){x.loading=!0;try{const H=await fetch("/api/exceptions/"+x.openExcId+"/resolve",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!H.ok)throw new Error("http "+H.status);showToast(t("exc-toast-resolved"),"success"),F(),await f(),await b(),a()}catch(H){console.warn("resolve fail",H),showToast(t("exc-toast-action-fail"),"error")}finally{x.loading=!1}}}async function B(){if(!(!x.openExcId||x.loading)){x.loading=!0;try{const H=await fetch("/api/exceptions/"+x.openExcId+"/ignore",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!H.ok)throw new Error("http "+H.status);showToast(t("exc-toast-ignored"),"success"),F(),await f(),await b(),a()}catch(H){console.warn("ignore fail",H),showToast(t("exc-toast-action-fail"),"error")}finally{x.loading=!1}}}let P=!1;async function Y(){if(P)return;const H=Array.from(e.selectedIds);if(H.length===0||!await showConfirm(n("exc-batch-confirm-resolve",{n:H.length})))return;P=!0;const g=showToast(n("exc-batch-count",{n:H.length})+" …","loading",0);try{const q=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:H,action:"resolve"})});if(!q.ok)throw new Error("http "+q.status);const N=await q.json();g(),showToast(n("exc-toast-batch-resolved",{n:N.processed||0}),"success"),e.selectedIds.clear(),await f(),await b(),a()}catch(q){g(),console.warn("batch resolve fail",q),showToast(t("exc-toast-batch-fail"),"error")}finally{P=!1}}async function G(){if(P)return;const H=Array.from(e.selectedIds);if(H.length===0||!await showConfirm(n("exc-batch-confirm-ignore",{n:H.length}),{danger:!1}))return;P=!0;const g=showToast(n("exc-batch-count",{n:H.length})+" …","loading",0);try{const q=await fetch("/api/exceptions/batch",{method:"POST",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||""),"Content-Type":"application/json"},body:JSON.stringify({ids:H,action:"ignore"})});if(!q.ok)throw new Error("http "+q.status);const N=await q.json();g(),showToast(n("exc-toast-batch-ignored",{n:N.processed||0,wl:N.whitelist_added||0}),"success"),e.selectedIds.clear(),await f(),await b(),a()}catch(q){g(),console.warn("batch ignore fail",q),showToast(t("exc-toast-batch-fail"),"error")}finally{P=!1}}function W(){e.selectedIds.clear(),d(e.listCache)}document.addEventListener("click",H=>{H.target.closest("#exc-drawer-close")&&F(),H.target.closest("#exc-drawer-mask")&&F(),H.target.closest("#exc-btn-resolve")&&D(),H.target.closest("#exc-btn-ignore")&&B(),H.target.closest("#exc-batch-resolve")&&Y(),H.target.closest("#exc-batch-ignore")&&G(),H.target.closest("#exc-batch-clear")&&W(),H.target.closest("#exc-loadmore")&&M()}),document.addEventListener("keydown",H=>{H.key==="Escape"&&x.openExcId&&F()}),document.addEventListener("click",H=>{H.target.closest("#btn-exc-refresh")&&(typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a())}),document.addEventListener("change",H=>{if(!H.target.closest("#exc-client-filter"))return;const E=H.target;e.currentClient=E.value||"",e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage(),a()}),document.addEventListener("click",H=>{const E=H.target.closest("#exc-status-tabs .exc-status-tab");if(!E)return;const g=E.dataset.status||"pending";g!==e.currentStatus&&(e.currentStatus=g,e.currentRule=null,e.selectedIds.clear(),e.listCache=[],typeof window.loadExceptionsPage=="function"&&window.loadExceptionsPage())}),window.addEventListener("online",()=>{e.loadFailed&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage&&window.loadExceptionsPage()}),setTimeout(a,1500),setInterval(a,6e4);function te(H){if(!H)return"—";try{const E=new Date(H),g=q=>String(q).padStart(2,"0");return`${E.getFullYear()}-${g(E.getMonth()+1)}-${g(E.getDate())} ${g(E.getHours())}:${g(E.getMinutes())}`}catch{return H.slice(0,16).replace("T"," ")}}async function re(){const H=document.getElementById("learned-list");if(H){H.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-loading"))}</div>`;try{const E=await fetch("/api/exception-whitelist",{headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!E.ok)throw new Error("http "+E.status);const q=(await E.json()).items||[];if(q.length===0){H.innerHTML=`<div class="learned-empty">${escapeHtml(t("set-learned-empty"))}</div>`;return}const N=`<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 4h8M5.5 4V2.5h3V4M4 4l0.6 8.5h4.8L10 4"/>
            </svg>`;H.innerHTML=q.map(K=>{const Z=t("exc-rule-"+K.rule_code)||K.rule_code;return`
                    <div class="learned-row" data-wl-id="${escapeHtml(String(K.id))}">
                        <div class="learned-seller" title="${escapeHtml(K.seller_name)}">${escapeHtml(K.seller_name)}</div>
                        <div class="learned-rule">${escapeHtml(Z)}</div>
                        <div class="learned-date">${escapeHtml(te(K.created_at))}</div>
                        <button class="learned-del-btn" data-del-wl="${escapeHtml(String(K.id))}" title="${escapeHtml(t("set-learned-del"))}" type="button">${N}</button>
                    </div>
                `}).join("")}catch(E){console.warn("loadLearnedRules fail",E),H.innerHTML=`<div class="learned-empty">${escapeHtml(t("exc-toast-load-fail"))}</div>`}}}window.loadLearnedRules=re,document.addEventListener("click",async H=>{const E=H.target.closest("[data-del-wl]");if(!E)return;const g=parseInt(E.dataset.delWl,10);if(!g)return;const q=E.closest(".learned-row"),N=q&&q.querySelector(".learned-seller"),K=N?N.textContent.trim():"",Z=t("set-learned-del-confirm").replace("{seller}",K);if(await showConfirm(Z,{danger:!0}))try{const ie=await fetch("/api/exception-whitelist/"+g,{method:"DELETE",headers:{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}});if(!ie.ok)throw new Error("http "+ie.status);showToast(t("set-learned-del-ok"),"success"),re(),typeof window.loadExceptionsPage=="function"&&document.getElementById("page-exceptions")?.classList.contains("show")&&window.loadExceptionsPage()}catch(ie){console.warn("delete whitelist fail",ie),showToast(t("set-learned-del-fail"),"error")}})})();(function(){let e={items:[],q:"",cat:"",selected:new Set,total:0,categories:{},pageSize:30,loading:!1,focusSearch:!1,searchCaret:0},n=null;function a(){return localStorage.getItem("mrpilot_token")||""}function o(p){const f=typeof currentLang=="string"&&currentLang||window._currentLang||"th",m=p.error_friendly&&p.error_friendly[f];if(m)return m;if(typeof humanizeError=="function"&&p.error_msg)try{return humanizeError(p.error_msg)}catch{}return t("erp-exc-reason-"+(p.category||"other"))}function s(){const p=document.getElementById("erp-exc-batch");if(!p)return;const f=e.selected.size;p.hidden=f===0;const m=p.querySelector(".erp-exc-batch-count");m&&(m.textContent=String(f))}function i(){const p=document.getElementById("erp-exc-block");if(!p)return;const f=e;if(!(f.total>0||!!f.q||!!f.cat)){p.hidden=!0,p.innerHTML="";return}p.hidden=!1;const b=f.categories||{},M=Object.keys(b).reduce((w,L)=>w+b[L],0);let I=`<button class="erp-exc-chip ${f.cat===""?"active":""}" data-erpexc-cat=""><span>${escapeHtml(t("erp-exc-cat-all"))}</span><span class="erp-exc-chip-count">${M}</span></button>`;Object.keys(b).forEach(w=>{I+=`<button class="erp-exc-chip ${f.cat===w?"active":""}" data-erpexc-cat="${escapeHtml(w)}"><span>${escapeHtml(t("erp-exc-cat-"+w))}</span><span class="erp-exc-chip-count">${b[w]}</span></button>`});const x=f.items||[],y=x.length>0&&x.every(w=>f.selected.has(w.id)),$=x.map(w=>{const L=w.state==="needs_action"?"needs":w.state==="retrying"?"retry":"fail",S=t("erp-exc-state-"+(w.state||"failed")),D=o(w),B=f.selected.has(w.id)?"checked":"";return`<div class="erp-exc-row" data-erpexc-id="${escapeHtml(w.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(w.id)}" ${B}></span>
                <span class="ex-inv" title="${escapeHtml(w.invoice_no||"")}">${escapeHtml(w.invoice_no||"—")}</span>
                <span class="ex-seller" title="${escapeHtml(w.seller_name||"")}">${escapeHtml(w.seller_name||"—")}</span>
                <span class="ex-buyer" title="${escapeHtml(w.ocr_buyer_name||"")}">${escapeHtml(w.ocr_buyer_name||"—")}</span>
                <span class="ex-state"><span class="erp-exc-state ${L}">${escapeHtml(S)}</span></span>
                <span class="ex-reason" title="${escapeHtml(D)}">${escapeHtml(D)}${w.error_code?` <span class="erp-exc-code">${escapeHtml(w.error_code)}</span>`:""}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(w.id)}">${escapeHtml(t("erp-exc-retry"))}</button></span>
            </div>`}).join(""),C=x.length===0?`<div class="erp-exc-empty">${escapeHtml(t("erp-exc-empty"))}</div>`:"",F=x.length<f.total?`<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t("erp-exc-load-more"))} (${x.length}/${f.total})</button>`:f.total>0?`<div class="erp-exc-count">${escapeHtml(t("erp-exc-shown",{n:x.length,total:f.total}))}</div>`:"";p.innerHTML=`
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t("erp-exc-title"))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t("erp-exc-sub"))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t("erp-exc-search-ph"))}" value="${escapeHtml(f.q)}">
            </div>
            <div class="erp-exc-chips">${I}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${f.selected.size?"":"hidden"}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${f.selected.size}</span> ${escapeHtml(t("erp-exc-batch-selected"))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t("erp-exc-batch-retry"))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t("erp-exc-batch-delete"))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t("erp-exc-batch-clear"))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${y?"checked":""}></span>
                    <span class="ex-inv">${escapeHtml(t("erp-exc-f-invoice"))}</span>
                    <span class="ex-seller">${escapeHtml(t("erp-exc-f-seller"))}</span>
                    <span class="ex-buyer">${escapeHtml(t("erp-exc-f-buyer"))}</span>
                    <span class="ex-state">${escapeHtml(t("erp-exc-f-state"))}</span>
                    <span class="ex-reason">${escapeHtml(t("erp-exc-f-reason"))}</span>
                    <span class="ex-act"></span>
                </div>
                ${$}${C}
            </div>
            <div class="erp-exc-foot">${F}</div>`;const j=document.getElementById("erp-exc-search");if(j){if(f.focusSearch){j.focus();try{j.setSelectionRange(f.searchCaret,f.searchCaret)}catch{}}j.addEventListener("input",()=>{f.q=j.value,f.focusSearch=!0,f.searchCaret=j.selectionStart||j.value.length,clearTimeout(n),n=setTimeout(()=>l(!1),350)}),j.addEventListener("blur",()=>{f.focusSearch=!1})}p.querySelectorAll(".erp-exc-chip").forEach(w=>{w.addEventListener("click",()=>{f.cat=w.dataset.erpexcCat||"",l(!1)})}),p.querySelectorAll("[data-erpexc-retry]").forEach(w=>{w.addEventListener("click",L=>{L.stopPropagation(),r(w.dataset.erpexcRetry,w)})}),p.querySelectorAll(".erp-exc-cb").forEach(w=>{w.addEventListener("change",()=>{const L=w.dataset.erpexcCb;w.checked?f.selected.add(L):f.selected.delete(L);const S=document.getElementById("erp-exc-cb-all");S&&(S.checked=x.length>0&&x.every(D=>f.selected.has(D.id))),s()})});const _=document.getElementById("erp-exc-cb-all");_&&_.addEventListener("change",()=>{x.forEach(w=>{_.checked?f.selected.add(w.id):f.selected.delete(w.id)}),p.querySelectorAll(".erp-exc-cb").forEach(w=>{w.checked=_.checked}),s()}),p.querySelectorAll("[data-erpexc-batch]").forEach(w=>{w.addEventListener("click",()=>u(w.dataset.erpexcBatch))});const h=document.getElementById("erp-exc-more");h&&h.addEventListener("click",()=>l(!0)),p.querySelectorAll(".erp-exc-row:not(.erp-exc-row-head)").forEach(w=>{w.addEventListener("click",L=>{L.target.closest("input,button")||typeof window._erpExcOpenEdit=="function"&&window._erpExcOpenEdit(w.dataset.erpexcId)})})}async function r(p,f){if(p){f&&(f.disabled=!0,f.textContent=t("erp-exc-retrying"));try{const m=await fetch("/api/erp/logs/"+encodeURIComponent(p)+"/retry",{method:"POST",headers:{Authorization:"Bearer "+a()}}),b=await m.json().catch(()=>({}));showToast(m.ok&&b.ok?t("erp-exc-retry-ok"):t("erp-exc-retry-fail"),m.ok&&b.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.delete(p),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function u(p){const f=Array.from(e.selected);if(p==="clear"){e.selected.clear(),i();return}if(f.length!==0){if(p==="delete"){if(!await showConfirm(t("erp-exc-batch-delete-confirm",{n:f.length}),{danger:!0}))return;try{const b=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:f.slice(0,200)})}),M=await b.json().catch(()=>({}));showToast(b.ok?t("erp-exc-batch-delete-ok",{n:M.deleted||0}):t("erp-exc-retry-fail"),b.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}}else if(p==="retry")try{const m=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({log_ids:f.slice(0,50)})}),b=await m.json().catch(()=>({}));showToast(m.ok?t("erp-exc-batch-retry-ok",{ok:b.succeeded||0,fail:(b.failed||0)+(b.skipped||0)}):t("erp-exc-retry-fail"),m.ok?"success":"error")}catch{showToast(t("erp-exc-retry-fail"),"error")}if(e.selected.clear(),l(!1),typeof window.refreshExcBadge=="function")try{window.refreshExcBadge()}catch{}}}async function l(p){const f=document.getElementById("erp-exc-block");if(!(!f||e.loading)){e.loading=!0;try{const m=new URLSearchParams;e.q&&m.set("q",e.q),e.cat&&m.set("category",e.cat),m.set("limit",String(e.pageSize)),m.set("offset",String(p?e.items.length:0));const b=await fetch("/api/erp/exceptions?"+m.toString(),{headers:{Authorization:"Bearer "+a()}});if(!b.ok){p||(f.hidden=!0);return}const M=await b.json(),I=M.items||[];e.items=p?e.items.concat(I):I,e.total=M.total||0,e.categories=M.categories||{},i()}catch{p||(f.hidden=!0)}finally{e.loading=!1}}}let d={};function c(){const p=document.getElementById("erp-exc-modal");p&&p.remove()}window._erpExcOpenEdit=function(p){const f=(e.items||[]).find(C=>String(C.id)===String(p));if(!f)return;const m=!!f.history_client_id&&f.category==="customer_mismatch",b=f.category==="product_mismatch"&&!!f.history_id&&!!f.endpoint_id,M=o(f),I=f.state==="needs_action"?"needs":f.state==="retrying"?"retry":"fail",x=(C,F)=>`<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(C)}</span><span class="erp-exc-m-v">${escapeHtml(F||"—")}</span></div>`;let y="";if(m)y=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-pick"))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t("erp-exc-edit-pick-ph"))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-pick-loading"))}</div>
                    </div>
                </div>`;else if(b)y=`
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t("erp-exc-edit-prod-intro"))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t("erp-exc-edit-prod-loading"))}</div>
                    </div>
                </div>`;else{const C="erp-exc-edit-hint-"+(f.category||"other");let F=t(C);(!F||F===C)&&(F=M),y=`<div class="erp-exc-m-hint">${escapeHtml(F)}</div>`}const $=document.createElement("div");if($.id="erp-exc-modal",$.className="erp-exc-modal-overlay",$.innerHTML=`
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t("erp-exc-edit-title"))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${I}">${escapeHtml(t("erp-exc-state-"+(f.state||"failed")))}</span> ${escapeHtml(M)}${f.error_code?` <span class="erp-exc-code">${escapeHtml(f.error_code)}</span>`:""}</div>
                    ${x(t("erp-exc-f-invoice"),f.invoice_no)}
                    ${x(t("erp-exc-f-seller"),f.seller_name)}
                    ${x(t("erp-exc-f-buyer"),f.ocr_buyer_name)}
                    ${x(t("erp-exc-edit-field-current"),f.client_name)}
                    ${y}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t("erp-exc-edit-close"))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t("erp-exc-edit-retry"))}</button>
                    ${m?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t("erp-exc-edit-bind-retry"))}</button>`:""}
                    ${b?`<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t("erp-exc-edit-bind-prod-retry"))}</button>`:""}
                </div>
            </div>`,document.body.appendChild($),$.addEventListener("click",C=>{C.target===$&&c()}),document.getElementById("erp-exc-m-close").addEventListener("click",c),document.getElementById("erp-exc-m-cancel").addEventListener("click",c),document.getElementById("erp-exc-m-retry").addEventListener("click",()=>{c(),r(f.id,null)}),m){let C="";const F=document.getElementById("erp-exc-m-bind"),j=document.getElementById("erp-exc-m-custlist"),_=document.getElementById("erp-exc-m-search"),h=(L,S)=>{const D=(S||"").trim().toLowerCase(),B=D?L.filter(P=>(P.code||"").toLowerCase().includes(D)||(P.name||"").toLowerCase().includes(D)):L;if(B.length===0){j.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-empty"))}</div>`;return}j.innerHTML=B.slice(0,100).map(P=>`<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(P.code||"")}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(P.name||"")}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(P.code||"")}</span>
                    </div>`).join(""),j.querySelectorAll(".erp-exc-m-cust").forEach(P=>{P.addEventListener("click",()=>{C=P.dataset.custCode||"",j.querySelectorAll(".erp-exc-m-cust").forEach(Y=>Y.classList.remove("sel")),P.classList.add("sel"),F&&(F.disabled=!C)})})},w=async()=>{const L=f.endpoint_id;if(d[L]){h(d[L],"");return}try{const S=await fetch("/api/erp/endpoints/"+encodeURIComponent(L)+"/customers",{headers:{Authorization:"Bearer "+a()}}),D=await S.json().catch(()=>({}));if(!S.ok||!D.ok){j.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`;return}const B=D.customers||[];d[L]=B,h(B,"")}catch{j.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-pick-fail"))}</div>`}};_&&_.addEventListener("input",()=>h(d[f.endpoint_id]||[],_.value)),w(),F&&F.addEventListener("click",async()=>{if(C){F.disabled=!0,F.textContent=t("erp-exc-retrying");try{if(!(await fetch("/api/erp/mappings/clients",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({client_id:f.history_client_id,erp_type:f.endpoint_adapter,erp_code:C})})).ok){showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry");return}showToast(t("erp-exc-edit-bound-ok"),"success"),c(),await r(f.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),F.disabled=!1,F.textContent=t("erp-exc-edit-bind-retry")}}})}if(b){const C=document.getElementById("erp-exc-m-bind-prod"),F=document.getElementById("erp-exc-m-prodlist"),j={};let _=[];const h=()=>'<option value="">'+escapeHtml(t("erp-exc-edit-prod-choose"))+"</option>"+_.slice(0,500).map(S=>`<option value="${escapeHtml(S.code||"")}" data-pname="${escapeHtml(S.name||"")}">`+escapeHtml((S.name||"")+" · "+(S.code||""))+"</option>").join(""),w=S=>{if(!S.length){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-noitems"))}</div>`;return}F.innerHTML=S.map(D=>`<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(D)}">${escapeHtml(D)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(D)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${h()}</select>
                    </div>`).join(""),F.querySelectorAll(".erp-exc-m-prod-sel").forEach(D=>{D.addEventListener("change",()=>{const B=D.dataset.item,P=D.options[D.selectedIndex];D.value?j[B]={code:D.value,name:P&&P.dataset.pname||""}:delete j[B],C&&(C.disabled=Object.keys(j).length===0)})})};(async()=>{try{const D=await(await fetch("/api/history/"+encodeURIComponent(f.history_id),{headers:{Authorization:"Bearer "+a()}})).json().catch(()=>({})),B=D&&D.pages||[],P=[],Y={};(Array.isArray(B)?B:[]).forEach(te=>{const re=te&&te.fields&&te.fields.items||[];(Array.isArray(re)?re:[]).forEach(H=>{const E=(H&&(H.name||H.description)||"").trim();E&&!Y[E]&&(Y[E]=1,P.push(E))})});const G=await fetch("/api/erp/endpoints/"+encodeURIComponent(f.endpoint_id)+"/products",{headers:{Authorization:"Bearer "+a()}}),W=await G.json().catch(()=>({}));if(!G.ok||!W.ok){F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`;return}_=W.products||[],w(P)}catch{F.innerHTML=`<div class="erp-exc-m-empty">${escapeHtml(t("erp-exc-edit-prod-fail"))}</div>`}})(),C&&C.addEventListener("click",async()=>{const S=Object.entries(j);if(S.length){C.disabled=!0,C.textContent=t("erp-exc-retrying");try{for(const[D,B]of S)if(!(await fetch("/api/erp/mappings/products",{method:"POST",headers:{Authorization:"Bearer "+a(),"Content-Type":"application/json"},body:JSON.stringify({erp_type:f.endpoint_adapter,item_name:D,erp_code:B.code,erp_name:B.name})})).ok){showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-prod-retry");return}showToast(t("erp-exc-edit-prod-bound-ok"),"success"),c(),await r(f.id,null)}catch{showToast(t("erp-exc-retry-fail"),"error"),C.disabled=!1,C.textContent=t("erp-exc-edit-bind-prod-retry")}}})}},window._rerenderErpExceptions=i,window.loadErpExceptions=l,window._erpExcState=e})();(function(){function e(p){try{if(location.search.indexOf("test_center=1")>=0||localStorage.getItem("pearnly_test_mode")==="1"||p&&p.id&&String(p.id)==="468b50c1-5593-4fd6-990d-515ce8085563")return!0}catch{}return!1}window.applyRoleVisibility=function(){var f=window._userInfo,m=!1,b=!0,M=!1,I=!1;f&&(m=typeof canManageTeam=="function"?canManageTeam(f):!!(f.role==="owner"||f.is_super_admin),b=typeof shouldHideMoney=="function"?shouldHideMoney(f):f.role==="member"&&!f.is_super_admin,M=typeof isSuperAdmin=="function"?isSuperAdmin(f):!!f.is_super_admin,I=e(f)),document.querySelectorAll("[data-show-if-team]").forEach(function(y){y.style.display=m?"":"none"}),document.querySelectorAll("[data-show-if-money]").forEach(function(y){y.style.display=b?"none":""}),document.querySelectorAll("[data-show-if-admin]").forEach(function(y){y.style.display=M?"":"none"}),document.querySelectorAll("[data-show-if-test]").forEach(function(y){y.style.display=I?"":"none"});var x=M||I;document.querySelectorAll("[data-show-if-special]").forEach(function(y){y.style.display=x?"":"none"})},window.renderAvatarMenu=function(f){if(f){var m=document.getElementById("avatar-btn"),b=document.getElementById("avatar-popup-name"),M=document.getElementById("avatar-popup-email");if(!(!m||!b||!M)){var I=(f.username||"").trim(),x=I.split("@")[0]||I||"—",y=(I.charAt(0)||"?").toUpperCase(),$=(f.avatar_url||"").trim();if($){var C=$.replace(/"/g,"&quot;"),F=y.replace(/'/g,"\\'");m.innerHTML='<img src="'+C+'" alt="'+y+`" referrerpolicy="no-referrer" onerror="this.parentNode.textContent='`+F+`'">`}else m.textContent=y;b.textContent=x,M.textContent=I||"—",m.setAttribute("title",I||"")}}};function n(){var p=document.getElementById("avatar-wrap"),f=document.getElementById("avatar-btn"),m=document.getElementById("avatar-popup");if(!p||!f||!m)return;function b(){m.classList.remove("show"),f.setAttribute("aria-expanded","false")}function M(){m.classList.add("show"),f.setAttribute("aria-expanded","true")}f.addEventListener("click",function(I){I.stopPropagation(),m.classList.contains("show")?b():M()}),document.addEventListener("click",function(I){m.classList.contains("show")&&!p.contains(I.target)&&b()}),m.addEventListener("click",function(I){var x=I.target.closest(".avatar-popup-item");if(x){var y=x.dataset.action;switch(b(),y){case"settings":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings");break;case"team":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("team")},50);break;case"billing":typeof openSettingsModal=="function"?openSettingsModal():typeof routeTo=="function"&&routeTo("settings"),setTimeout(function(){typeof switchSettingsTab=="function"&&switchSettingsTab("plan")},50);break;case"shortcuts":if(typeof showToast=="function"){var $=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast($||"即将上线","info")}break;case"admin":window.location.href="/admin/cost";break;case"test-center":typeof routeTo=="function"&&routeTo("test-center");break;case"help":var C=document.getElementById("help-modal");C&&(C.style.display="flex");break;case"logout":try{localStorage.removeItem("mrpilot_token")}catch{}try{localStorage.removeItem("mrpilot_user")}catch{}window.location.href="/";break}}}),window._closeAvatarPopup=b}function a(){return[].slice.call(document.querySelectorAll(".cmdk-item")).filter(function(p){return p.style.display!=="none"})}function o(p){var f=a();f.forEach(function(m){m.classList.remove("focus")}),f[p]&&(f[p].classList.add("focus"),f[p].scrollIntoView({block:"nearest"}))}function s(p){var f=a();if(f.length){var m=f.findIndex(function(M){return M.classList.contains("focus")});m<0&&(m=0);var b=(m+p+f.length)%f.length;o(b)}}function i(p){p=(p||"").toLowerCase().trim();var f=0,m=window._userInfo,b=typeof isSuperAdmin=="function"?isSuperAdmin(m):!!(m&&m.is_super_admin),M=e(m);document.querySelectorAll(".cmdk-item").forEach(function(x){if(x.dataset.showIfAdmin==="1"&&!b){x.style.display="none";return}if(x.dataset.showIfTest==="1"&&!M){x.style.display="none";return}var y=(x.dataset.cmdkText||x.textContent||"").toLowerCase(),$=!p||y.indexOf(p)>=0;x.style.display=$?"":"none",x.classList.remove("focus"),$&&f++}),document.querySelectorAll("[data-cmdk-section]").forEach(function(x){for(var y=x.nextElementSibling,$=!1;y&&!y.hasAttribute("data-cmdk-section");){if(y.classList&&y.classList.contains("cmdk-item")&&y.style.display!=="none"){$=!0;break}y=y.nextElementSibling}x.style.display=$?"":"none"});var I=document.getElementById("cmdk-empty");I&&(I.style.display=f===0?"flex":"none"),o(0)}window.openCmdk=function(){var f=document.getElementById("cmdk-mask");f&&(typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup(),f.classList.add("show"),typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility(),setTimeout(function(){var m=document.getElementById("cmdk-input");m&&(m.value="",i(""),m.focus(),o(0))},50))},window.closeCmdk=function(){var f=document.getElementById("cmdk-mask");f&&f.classList.remove("show")};function r(p){if(p){if(p.classList.contains("cmdk-item-locked")){if(typeof showToast=="function"){var f=typeof t=="function"?t("feature-coming-soon"):"即将上线";showToast(f||"即将上线","info")}return}var m=p.dataset.cmdkRoute,b=p.dataset.cmdkAction;if(window.closeCmdk(),m){typeof routeTo=="function"&&routeTo(m);return}if(b){if(b==="open-admin"){window.location.href="/admin/cost";return}if(b.indexOf("lang-")===0){var M=b.slice(5);typeof applyLang=="function"&&applyLang(M)}}}}function u(){var p=document.getElementById("cmdk-mask"),f=document.getElementById("cmdk-input"),m=document.getElementById("cmdk-body");if(!(!p||!f||!m)){p.addEventListener("click",function(I){I.target===p&&window.closeCmdk()});var b=document.getElementById("cmdk-esc-btn");b&&b.addEventListener("click",function(){window.closeCmdk()}),f.addEventListener("input",function(I){i(I.target.value)}),f.addEventListener("keydown",function(I){I.key==="ArrowDown"?(I.preventDefault(),s(1)):I.key==="ArrowUp"?(I.preventDefault(),s(-1)):I.key==="Enter"?(I.preventDefault(),r(p.querySelector(".cmdk-item.focus"))):I.key==="Escape"&&(I.preventDefault(),window.closeCmdk())}),m.addEventListener("click",function(I){var x=I.target.closest(".cmdk-item");x&&r(x)}),m.addEventListener("mousemove",function(I){var x=I.target.closest(".cmdk-item");!x||x.style.display==="none"||x.classList.contains("cmdk-item-locked")||(a().forEach(function(y){y.classList.remove("focus")}),x.classList.add("focus"))});var M=document.getElementById("topbar-search");M&&(M.addEventListener("click",function(){window.openCmdk()}),M.addEventListener("keydown",function(I){(I.key==="Enter"||I.key===" ")&&(I.preventDefault(),window.openCmdk())}))}}document.addEventListener("keydown",function(p){if((p.metaKey||p.ctrlKey)&&(p.key==="k"||p.key==="K")){p.preventDefault(),window.openCmdk();return}if(p.key==="Escape"){var f=document.getElementById("cmdk-mask");if(f&&f.classList.contains("show")){window.closeCmdk();return}var m=document.getElementById("avatar-popup");m&&m.classList.contains("show")&&typeof window._closeAvatarPopup=="function"&&window._closeAvatarPopup()}});try{var l=(navigator.userAgent||"").toLowerCase(),d=l.indexOf("mac")>=0||l.indexOf("iphone")>=0||l.indexOf("ipad")>=0;d||document.body.classList.add("is-windows")}catch{}function c(){n(),u(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("nav-ia-phase1-role",function(){try{typeof window.applyRoleVisibility=="function"&&window.applyRoleVisibility()}catch{}})}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c()})();(function(){function n(b){return String(b??"").replace(/[&<>"']/g,function(M){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[M]})}function a(b){if(!b||isNaN(b))return"";var M=Number(b);return M<1024?M+" B":M<1024*1024?(M/1024).toFixed(1)+" KB":(M/1024/1024).toFixed(1)+" MB"}document.addEventListener("click",function(b){var M=b.target.closest&&b.target.closest(".recon-collapse-head");if(M&&!(b.target.closest("button")||b.target.closest("a"))){var I=M.closest(".recon-collapse");if(I){var x=I.getAttribute("data-collapsed")==="true";I.setAttribute("data-collapsed",x?"false":"true"),x&&(I.id==="vex-summary-collapse"&&c(),I.id==="vex-detail-collapse"&&p())}}}),document.addEventListener("keydown",function(b){if(!(b.key!=="Enter"&&b.key!==" ")){var M=b.target.closest&&b.target.closest(".recon-collapse-head");M&&(b.preventDefault(),M.click())}});var o={vat:"",gl:""};window._glvClearPreviewSearch=function(){o.vat="",o.gl=""};var s='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',i='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function r(){l("vat"),l("gl")}function u(b){try{if(typeof window._glvPreviewFiles=="function")return window._glvPreviewFiles(b)||[]}catch{}var M=document.getElementById(b==="vat"?"glv-vat-input":"glv-gl-input");return M&&M.files?Array.from(M.files):[]}function l(b){var M=document.getElementById(b==="vat"?"glv-pp-vat-col":"glv-pp-gl-col");if(M){var I=u(b),x=b==="vat"?"glv-up-vat-title":"glv-up-gl-title",y=b==="vat"?"① 销项税报告":"② 总账 GL",$=window.t&&window.t(x)||y,C=n(window.t&&window.t("vex-preview-search")||"搜索文件名..."),F=n(window.t&&window.t("vex-preview-clear-all")||"全清"),j=o[b]||"",_=I.length;M.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+n($)+' <span class="vex-pp-col-count">'+_+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="glv-pp-search-'+b+'" type="text" placeholder="'+C+'" value="'+n(j)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="glv-pp-clearall-'+b+'" type="button">'+F+'</button></div><div class="vex-pp-file-list" id="glv-pp-'+b+'-list"></div><div class="vex-pp-pagination" id="glv-pp-'+b+'-pg"></div>';var h=document.getElementById("glv-pp-search-"+b);h&&h.addEventListener("input",function(L){o[b]=L.target.value,d(b)});var w=document.getElementById("glv-pp-clearall-"+b);w&&w.addEventListener("click",function(){window._glvRemoveFile&&window._glvRemoveFile(b)}),d(b)}}function d(b){var M=document.getElementById("glv-pp-"+b+"-list"),I=document.getElementById("glv-pp-"+b+"-pg");if(M){var x=u(b),y=(o[b]||"").toLowerCase(),$=x.map(function(j,_){return{f:j,i:_}}),C=y?$.filter(function(j){return j.f.name.toLowerCase().indexOf(y)>=0}):$;if(M.innerHTML=C.map(function(j){var _=j.f;return'<div class="vex-pp-file-row">'+s+'<span class="vex-pp-fi-name" title="'+n(_.name)+'">'+n(_.name)+'</span><span class="vex-pp-fi-size">'+a(_.size)+'</span><button class="vex-pp-fi-del" type="button" data-kind="'+b+'" data-idx="'+j.i+'" aria-label="remove">'+i+"</button></div>"}).join(""),M.querySelectorAll(".vex-pp-fi-del").forEach(function(j){j.addEventListener("click",function(){var _=j.dataset.kind,h=parseInt(j.dataset.idx,10);window._glvRemoveFile&&window._glvRemoveFile(_,isNaN(h)?null:h)})}),I){var F=window.t&&window.t("vex-preview-count")||"显示前 {n} / 共 {m}";I.textContent=F.replace("{n}",C.length).replace("{m}",C.length)}}}function c(){var b=function(I,x){var y=document.getElementById(I);y&&(y.textContent=x==null?"—":String(x))},M=window._vexLastTask||{};b("vex-sum-total",M.total),b("vex-sum-matched",M.matched),b("vex-sum-diff",M.diff),b("vex-sum-incomplete",M.incomplete),b("vex-sum-cash",M.cash),document.getElementById("vex-summary-sub")}function p(){var b=window._vexLastTask&&window._vexLastTask.diff_rows||[],M=document.getElementById("vex-detail-tbody"),I=document.getElementById("vex-detail-table"),x=document.getElementById("vex-detail-empty");if(!(!M||!I||!x)){if(b.length===0){I.style.display="none",x.style.display="";return}x.style.display="none",I.style.display="";var y=b.map(function(C){return'<tr><td class="recon-detail-cell-mono">'+n(C.invoice_no||"")+"</td><td>"+n(C.field||"")+"</td><td>"+n(C.report_value||"")+"</td><td>"+n(C.invoice_value||"")+"</td><td>"+n(C.kind||"")+"</td></tr>"}).join("");M.innerHTML=y;var $=document.getElementById("vex-detail-sub");$&&($.textContent=String(b.length))}}function f(){var b=document.getElementById("glv-toggle-preview");b&&!b._reconBound&&(b._reconBound=!0,b.addEventListener("click",function(){var M=document.getElementById("glv-preview-panel"),I=document.getElementById("glv-toggle-preview-label"),x=M&&M.style.display!=="none";M&&(M.style.display=x?"none":""),b.classList.toggle("open",!x),I&&(I.textContent=x?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),x||r()})),["glv-vat-input","glv-gl-input"].forEach(function(M){var I=document.getElementById(M);!I||I._reconWatched||(I._reconWatched=!0,I.addEventListener("change",function(){var x=document.getElementById("glv-preview-panel");x&&x.style.display!=="none"&&r()}))})}function m(){var b=document.getElementById("vex-summary-collapse"),M=document.getElementById("vex-detail-collapse");b&&(b.style.display=""),M&&(M.style.display=""),c(),p()}window._fillVexSummary=c,window._fillVexDetail=p,window._onVexResultShown=m,document.addEventListener("DOMContentLoaded",function(){f()}),setTimeout(f,1500),typeof window.subscribeI18n=="function"&&window.subscribeI18n("recon-collapse",function(){var b=document.getElementById("glv-preview-panel");b&&b.style.display!=="none"&&r();var M=document.getElementById("glv-toggle-preview-label"),I=document.getElementById("glv-toggle-preview");M&&I&&(M.textContent=I.classList.contains("open")?window.t&&window.t("vex-toggle-preview-close")||"收起清单":window.t&&window.t("vex-toggle-preview-open")||"查看清单")}),window._reconCollapse={renderGlvPreview:r,fillVexSummary:c,fillVexDetail:p}})();(function(){function e(i){}function n(){const i=document.querySelectorAll("[data-recon-tab]");i.forEach(u=>{u.addEventListener("click",()=>{i.forEach(f=>f.classList.remove("active")),u.classList.add("active");const l=u.dataset.reconTab,d=document.getElementById("recon-pane-bank"),c=document.getElementById("recon-pane-sale-vat"),p=document.getElementById("recon-pane-gl-vat");d&&(d.style.display=l==="bank"?"":"none"),c&&(c.style.display=l==="sale-vat"?"":"none"),p&&(p.style.display=l==="gl-vat"?"":"none"),l==="gl-vat"&&window.GlVatRecon&&window.GlVatRecon.ensureInit(),l==="bank"&&typeof window._bankReconV2Init=="function"&&window._bankReconV2Init()})});const r=document.querySelector("[data-recon-tab].active");r&&(r.dataset.reconTab,void 0)}function a(){const i=document.getElementById("page-settings");if(!i)return null;let r=document.getElementById("settings-modal-overlay");if(r)return r;r=document.createElement("div"),r.id="settings-modal-overlay",r.className="settings-modal-overlay",r.style.display="none",i.parentElement.insertBefore(r,i),r.appendChild(i);const u=document.createElement("button");return u.id="settings-modal-close",u.className="settings-modal-close",u.setAttribute("aria-label","close"),u.innerHTML='<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 5l10 10M15 5L5 15"/></svg>',i.insertBefore(u,i.firstChild),u.addEventListener("click",s),r.addEventListener("click",l=>{l.target===r&&s()}),r}function o(){const i=a();if(!i)return;i.style.display="flex",document.body.classList.add("settings-modal-open");const r=document.getElementById("page-settings");r&&(r.style.display="block"),setTimeout(()=>{try{typeof renderSettings=="function"&&renderSettings()}catch(l){console.warn("renderSettings:",l)}let u=document.querySelector(".settings-tab.active")||document.querySelector('.settings-tab[data-tab="profile"]');u&&u.click()},50)}function s(){const i=document.getElementById("settings-modal-overlay");i&&(i.style.display="none"),document.body.classList.remove("settings-modal-open")}window.openSettingsModal=o,window.closeSettingsModal=s,document.addEventListener("keydown",i=>{if(i.key==="Escape"){const r=document.getElementById("settings-modal-overlay");r&&r.style.display==="flex"&&s()}}),window.addEventListener("hashchange",()=>{location.hash==="#/settings"&&o()}),window.addEventListener("DOMContentLoaded",()=>{location.hash==="#/settings"&&o()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n()})();(function(){const a=/\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i,o=V=>document.getElementById(V);function s(){return{Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")}}function i(V){return String(V??"").replace(/[&<>"']/g,Q=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[Q])}function r(V){return V<1024?V+" B":V<1024*1024?(V/1024).toFixed(1)+" KB":(V/1024/1024).toFixed(1)+" MB"}let u=[],l=[],d=!1,c=[],p=50,f=50,m="",b="";async function M(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=1",{headers:s()});if(!V.ok)return;const ee=(await V.json()).kpi||{};[["vex-kpi-month-val",ee.this_month],["vex-kpi-running-val",ee.running],["vex-kpi-done-val",ee.done],["vex-kpi-failed-val",ee.failed]].forEach(([ne,oe])=>{const ue=document.getElementById(ne);ue&&(ue.textContent=oe??0)})}catch{}}async function I(){try{const V=await fetch("/api/vat_excel/tasks?page=1&page_size=100",{headers:s()});if(!V.ok)return;const Q=await V.json();C(Q.rows||[])}catch{}}const x=10;var y=1;function $(){var V=((document.getElementById("vex-task-search")||{}).value||"").trim().toLowerCase();if(y=1,C(c),!!V){var Q=document.getElementById("vex-task-tbody");Q&&Q.querySelectorAll("tr").forEach(function(ee){ee.dataset.taskId&&(ee.style.display=ee.textContent.toLowerCase().indexOf(V)>=0?"":"none")})}}function C(V){c=V||c;const Q=document.getElementById("vex-task-tbody");if(!Q)return;if(!c.length){Q.innerHTML='<tr><td colspan="9" class="vex-task-empty">'+(t("sv-empty-title")||"还没有对账任务")+"</td></tr>",F(0);return}const ee=Math.ceil(c.length/x);y>ee&&(y=ee);const ne=(y-1)*x;j(c.slice(ne,ne+x)),F(c.length)}function F(V){const Q=document.getElementById("vex-task-pager"),ee=document.getElementById("vex-task-pager-info"),ne=document.getElementById("vex-task-prev"),oe=document.getElementById("vex-task-next");if(!Q)return;if(V<=x){Q.style.display="none";return}Q.style.display="";const ue=Math.ceil(V/x);ee&&(ee.textContent=y+" / "+ue),ne&&(ne.disabled=y<=1),oe&&(oe.disabled=y>=ue)}function j(V){const Q=document.getElementById("vex-task-tbody");if(!Q)return;const ee={pending:t("vex-status-pending")||"待处理",running:t("vex-status-running")||"处理中",done:t("vex-status-done")||"已完成",failed:t("vex-status-failed")||"失败"},ne={pending:"badge-gray",running:"badge-blue",done:"badge-green",failed:"badge-red"},oe='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ue='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>';Q.innerHTML=V.map(k=>{const T=k.created_at?new Date(k.created_at).toLocaleString([],{year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}):"—",A=k.period||"—",U=k.matched_count!=null?k.matched_count+" ✓ · "+k.mismatched_count+" ⚠":"—",z=k.mismatch_amount!=null?"฿ "+Number(k.mismatch_amount).toLocaleString():"—",v=k.elapsed_seconds!=null?k.elapsed_seconds.toFixed(1)+" s":"—",R=k.status||"pending",O=k.client_name&&k.client_name!=="client"?k.client_name:t("vex-client-all")||"全部客户";return`<tr class="vex-task-row" data-task-id="${i(k.id)}" style="cursor:pointer">
                <td>${T}</td>
                <td>${i(O)}</td>
                <td>${i(A)}</td>
                <td>${(k.invoice_count||0)+" / "+(k.report_count||0)}</td>
                <td>${U}</td>
                <td>${z}</td>
                <td><span class="badge ${ne[R]||"badge-gray"}">${ee[R]||R}</span></td>
                <td>${v}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${i(k.id)}" title="${t("hist_export")||"导出"}">${oe}</button>
                    <button class="vex-task-del-btn" data-task-id="${i(k.id)}" title="${t("vex-task-delete-confirm-title")||"删除"}">${ue}</button>
                </div></td>
            </tr>`}).join(""),Q.querySelectorAll(".vex-task-dl-btn").forEach(k=>{k.addEventListener("click",async T=>{T.stopPropagation();const A=k.dataset.taskId;try{const U=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(A)+"/download",{credentials:"include",headers:s()});if(U.status===410){showToast(t("vex-toast-expired")||"数据已过期 · 请重新对账","warn");return}if(!U.ok){showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error");return}const z=await U.blob(),R=(U.headers.get("Content-Disposition")||"").match(/filename\*?=(?:UTF-8''|")?([^";]+)/i),O=R?decodeURIComponent(R[1]):"vat_recon_"+A+".xlsx",J=URL.createObjectURL(z),X=document.createElement("a");X.href=J,X.download=O,X.click(),setTimeout(()=>URL.revokeObjectURL(J),1e3)}catch{showToast(t("vex-toast-dl-fail")||"下载失败 · 请重试","error")}})}),Q.querySelectorAll(".vex-task-del-btn").forEach(k=>{k.addEventListener("click",T=>{T.stopPropagation(),h(k.dataset.taskId)})}),$()}function _(){var V=document.getElementById("vex-task-prev"),Q=document.getElementById("vex-task-next");V&&!V._vexBound&&(V._vexBound=!0,V.addEventListener("click",function(){y>1&&(y--,C())})),Q&&!Q._vexBound&&(Q._vexBound=!0,Q.addEventListener("click",function(){var ee=Math.ceil(c.length/x);y<ee&&(y++,C())}))}async function h(V){const Q=t("vex-task-delete-confirm-title")||"删除对账任务?",ee=t("vex-task-delete-confirm-body")||"同时清掉对应的发票识别缓存 · 不可恢复";if(await showConfirm(ee,{title:Q,danger:!0,okText:t("vex-task-delete-confirm-title")||"确认删除"}))try{const oe=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{method:"DELETE",credentials:"include",headers:s()});if(!oe.ok)throw new Error(oe.status);showToast(t("vex-task-delete-ok")||"已删除","success"),I(),M()}catch{showToast(t("vex-task-delete-fail")||"删除失败","error")}}function w(V){const Q=window._currentLang||"th",ee={zh:`已忽略 ${V} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,th:`ข้ามไฟล์ที่ไม่รองรับ ${V} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,en:`Ignored ${V} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,ja:`非対応ファイル ${V} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`};showToast(ee[Q]||ee.th,"warn")}function L(V){const Q=new Set(u.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),u.push(ne),u.length>=1e3))break}ee>0&&w(ee),u.length>1e3&&(u=u.slice(0,1e3),showToast(t("vex-toast-cap-inv"),"warn")),P()}function S(V){const Q=new Set(l.map(ne=>ne.name+"|"+ne.size));let ee=0;for(const ne of V){if(!a.test(ne.name)){ee++;continue}const oe=ne.name+"|"+ne.size;if(!Q.has(oe)&&(Q.add(oe),l.push(ne),l.length>=30))break}ee>0&&w(ee),l.length>30&&(l=l.slice(0,30),showToast(t("vex-toast-cap-rep"),"warn")),P()}function D(V){u.splice(V,1),P()}function B(V){l.splice(V,1),P()}function P(){const V=o("vex-list-invoice"),Q=o("vex-list-report"),ee=o("vex-count-invoice"),ne=o("vex-count-report");ee&&(ee.textContent=u.length),ne&&(ne.textContent=l.length);const oe=(T,A,U)=>`<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${i(T.name)}">${i(T.name)}</span>
            <span class="vex-fi-s">${r(T.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${U}" data-vex-idx="${A}" aria-label="remove">×</button>
        </div>`;V&&(V.innerHTML=u.map((T,A)=>oe(T,A,"inv")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),Q&&(Q.innerHTML=l.map((T,A)=>oe(T,A,"rep")).join("")||'<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>'),document.querySelectorAll(".vex-fi-x").forEach(T=>{T.addEventListener("click",A=>{const U=T.dataset.vexKind,z=parseInt(T.dataset.vexIdx,10);U==="inv"?D(z):B(z)})});const ue=u.length>0&&l.length>0;o("vex-build").disabled=!ue||d;const k=o("vex-action-info");k&&(!u.length||!l.length?(k.textContent=t("vex-need-both")||"需要至少 1 张发票 + 1 份 VAT 报告",k.className="vex-action-info muted"):(k.textContent=(t("vex-ready")||"已就绪 · {a} 张发票 · {b} 份报告").replace("{a}",u.length).replace("{b}",l.length),k.className="vex-action-info ok")),te()}const Y='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>',G='<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',W='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';function te(){const V=o("vex-preview-panel");if(!V||V.style.display==="none")return;re("inv"),re("rep");const Q=o("vex-pp-guide");Q&&(Q.style.display=u.length>100?"flex":"none")}function re(V){const Q=o(V==="inv"?"vex-pp-invoice-col":"vex-pp-report-col");if(!Q)return;const ee=V==="inv"?u:l,ne=V==="inv"?m:b,oe=t(V==="inv"?"vex-preview-invoice":"vex-preview-report")||(V==="inv"?"销售发票":"VAT 报告"),ue=i(t("vex-preview-search")||"搜索文件名..."),k=i(t("vex-preview-clear-all")||"全清");Q.innerHTML=`
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${i(oe)} <span class="vex-pp-col-count">${ee.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${V}" type="text"
                       placeholder="${ue}" value="${i(ne)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${V}" type="button">${k}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${V}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${V}-pg"></div>`;const T=o("vex-pp-search-"+V);T&&T.addEventListener("input",U=>{V==="inv"?(m=U.target.value,p=50):(b=U.target.value,f=50),H(V)});const A=o("vex-pp-clearall-"+V);A&&A.addEventListener("click",()=>{V==="inv"?(u=[],m="",p=50):(l=[],b="",f=50),P()}),H(V)}function H(V){const Q=o("vex-pp-"+V+"-list"),ee=o("vex-pp-"+V+"-pg");if(!Q)return;const ne=V==="inv"?u:l,oe=V==="inv"?m:b,ue=V==="inv"?p:f,k=V==="inv"?Y:G,T=ne.map((z,v)=>({f:z,i:v})),A=oe?T.filter(({f:z})=>z.name.toLowerCase().includes(oe.toLowerCase())):T,U=A.slice(0,ue);if(Q.innerHTML=U.map(({f:z,i:v})=>`
            <div class="vex-pp-file-row">
                ${k}
                <span class="vex-pp-fi-name" title="${i(z.name)}">${i(z.name)}</span>
                <span class="vex-pp-fi-size">${r(z.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${V}" data-ridx="${v}" aria-label="remove">${W}</button>
            </div>`).join("")+`<div id="vex-pp-sentinel-${V}" style="height:1px;flex-shrink:0"></div>`,Q.querySelectorAll(".vex-pp-fi-del").forEach(z=>{z.addEventListener("click",()=>{const v=parseInt(z.dataset.ridx,10);z.dataset.kind==="inv"?D(v):B(v)})}),ee){const z=t("vex-preview-count")||"显示前 {n} / 共 {m}";ee.textContent=z.replace("{n}",U.length).replace("{m}",A.length)}E(V,A.length)}function E(V,Q){if((V==="inv"?p:f)>=Q)return;const ne=o("vex-pp-sentinel-"+V),oe=o("vex-pp-"+V+"-list");if(!ne||!oe)return;const ue=new IntersectionObserver(k=>{k[0].isIntersecting&&(ue.disconnect(),V==="inv"?p+=50:f+=50,H(V))},{root:oe,threshold:.8});ue.observe(ne)}function g(V,Q,ee,ne){const oe=o(V),ue=o(Q);!oe||!ue||(oe.addEventListener("click",()=>ue.click()),oe.addEventListener("keydown",k=>{(k.key==="Enter"||k.key===" ")&&(k.preventDefault(),ue.click())}),oe.addEventListener("dragover",k=>{k.preventDefault(),oe.classList.add("drag-over")}),oe.addEventListener("dragleave",()=>oe.classList.remove("drag-over")),oe.addEventListener("drop",k=>{k.preventDefault(),oe.classList.remove("drag-over");const A=Array.from(k.dataTransfer.files).filter(U=>a.test(U.name));if(!A.length){showToast(t("vex-toast-bad-ext"),"error");return}ee(A)}),ue.addEventListener("change",()=>{const k=Array.from(ue.files);ee(k),ue.value=""}))}async function q(){if(d||!u.length||!l.length)return;d=!0,o("vex-build").disabled=!0,o("vex-progress").style.display="flex";var V=document.getElementById("vex-download");V&&(V.style.display="none"),["vex-summary-collapse","vex-detail-collapse"].forEach(function(oe){var ue=document.getElementById(oe);ue&&(ue.style.display="none")});const Q=Date.now();o("vex-progress-title").textContent=t("vex-progress-running")||"AI 抽取中",o("vex-progress-sub").textContent=(t("vex-progress-sub")||"{a} 张发票 + {b} 份报告 · 并行处理").replace("{a}",u.length).replace("{b}",l.length);const ee=setInterval(()=>{const oe=Math.floor((Date.now()-Q)/1e3);o("vex-progress-sub").textContent=(t("vex-progress-elapsed")||"已 {s} 秒 · {a} 张发票 + {b} 份报告").replace("{s}",oe).replace("{a}",u.length).replace("{b}",l.length)},1e3);try{const oe=new FormData;for(const pe of u)oe.append("invoices",pe);for(const pe of l)oe.append("reports",pe);const ue=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";oe.append("lang",ue);const k=localStorage.getItem("mrpilot_token")||"",T=await fetch("/api/vat_excel/submit",{method:"POST",headers:s(),body:oe});let A=null;try{A=await T.json()}catch{A=null}if(!T.ok||!A||!A.ok||!A.job_id)throw clearInterval(ee),new Error(A&&A.detail||"HTTP "+T.status);const U=o("vex-progress-sub"),z=await window._reconPollJob(A.job_id,k,{onProgress:pe=>{U&&(U.textContent=window._reconProgressText(pe,ue))}});if(clearInterval(ee),!z||z.status!=="done"||!z.result_id)throw new Error(t("vex-toast-fail")||"生成失败");const v=z.result_id;let R=0;const O=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(v)+"/download",{headers:s()});if(!O.ok)throw new Error("HTTP "+O.status);const X=(O.headers.get("Content-Disposition")||"").match(/filename="([^"]+)"/),de=X&&X[1]||"vat_recon_"+Date.now()+".xlsx",se=await O.blob(),ce=URL.createObjectURL(se),ae=o("vex-download");ae.href=ce,ae.download=de;try{const pe=document.createElement("a");pe.href=ce,pe.download=de,document.body.appendChild(pe),pe.click(),setTimeout(()=>pe.remove(),100)}catch{}o("vex-progress").style.display="none";var ne=document.getElementById("vex-download");ne&&(ne.style.display=""),v&&(R=await Z(v)),window._onVexResultShown&&window._onVexResultShown(),R>0?showToast((t("vex-toast-some-fail")||"有 {n} 张发票 OCR 失败").replace("{n}",R),"warn"):showToast(t("vex-toast-done")||"Excel 已生成","success"),M(),setTimeout(I,800)}catch(oe){clearInterval(ee),o("vex-progress").style.display="none";const ue=(t("vex-toast-fail")||"生成失败")+": "+(oe.message||oe);showToast(ue,"error")}finally{d=!1,o("vex-build").disabled=!1}}function N(){u=[],l=[];var V=document.getElementById("vex-download");V&&(V.style.display="none"),P()}function K(V){if(V==null)return"—";var Q=parseFloat(V);return isNaN(Q)?"—":Q.toLocaleString("th-TH",{minimumFractionDigits:2,maximumFractionDigits:2})}async function Z(V){try{var Q=await fetch("/api/vat_excel/tasks/"+encodeURIComponent(V),{headers:s()});if(!Q.ok)throw new Error(Q.status);var ee=await Q.json(),ne=ee.raw_data_json;if(typeof ne=="string")try{ne=JSON.parse(ne)}catch{ne={}}ne=ne||{};var oe=ne.rows||[],ue=[];oe.forEach(function(A){A.kind==="invoice_orphan"?ue.push({invoice_no:A.invoice_no||"",field:"仅发票有",report_value:"—",invoice_value:K(A.amount_inv),kind:A.kind}):A.kind==="report_orphan"?ue.push({invoice_no:A.invoice_no||"",field:"仅报告有",report_value:K(A.amount_rep),invoice_value:"—",kind:A.kind}):A.dims&&Object.keys(A.dims).length>0&&Object.keys(A.dims).forEach(function(U){var z=String(A.dims[U]||""),v=z.split(" ≠ ");ue.push({invoice_no:A.invoice_no||"",field:U,report_value:v[0]||z,invoice_value:v.length>1?v[1]:"—",kind:"diff"})})});var k=oe.filter(function(A){return A.kind==="matched_cash"}).length,T=Math.max(0,parseInt(ne.invoice_ocr_failed_count||0,10));return window._vexLastTask={total:ne.n_total||0,matched:ne.n_ok||0,diff:ne.n_diff||0,incomplete:T,cash:k,diff_rows:ue,task_id:V},window._fillVexSummary&&window._fillVexSummary(),window._fillVexDetail&&window._fillVexDetail(),T}catch{return 0}}function le(){const V=document.getElementById("vex-pane");V&&V.querySelectorAll("[data-i18n]").forEach(Q=>{const ee=t(Q.dataset.i18n);ee&&(Q.textContent=ee)}),P(),I()}function ie(){g("vex-drop-invoice","vex-input-invoice",L),g("vex-drop-report","vex-input-report",S);const V=o("vex-build"),Q=o("vex-reset");V&&V.addEventListener("click",q),Q&&Q.addEventListener("click",N),document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach(oe=>{oe.addEventListener("click",()=>{M(),I()})}),_();const ee=document.getElementById("vex-task-search");ee&&ee.addEventListener("input",$);const ne=document.getElementById("vex-toggle-preview");ne&&ne.addEventListener("click",()=>{const oe=o("vex-preview-panel"),ue=o("vex-toggle-preview-label"),k=oe&&oe.style.display!=="none";oe&&(oe.style.display=k?"none":""),ne&&ne.classList.toggle("open",!k),ue&&(ue.textContent=k?t("vex-toggle-preview-open")||"查看清单":t("vex-toggle-preview-close")||"收起清单"),k||te()}),P(),M()}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ie):ie(),typeof window.subscribeI18n=="function"&&(window.subscribeI18n("vex-excel",le),window.subscribeI18n("vex-preview-panel",te))})();(function(){const e=E=>document.getElementById(E),n=()=>localStorage.getItem("mrpilot_token")||"",a=()=>typeof window.currentLang=="string"&&window.currentLang?window.currentLang:localStorage.getItem("mrpilot_lang")||"th",o=()=>({Authorization:"Bearer "+n()}),s={inited:!1,glFile:[],vatFile:[],running:!1,currentTaskId:null,lastDetail:[],lastSummary:null},i={th:{not_found:"ไม่พบข้อมูล",running:"กำลังกระทบยอด…",error:"เกิดข้อผิดพลาด",need_files:"กรุณาเลือกไฟล์ทั้งสอง",done:"เสร็จสิ้น",hint_need_both:"อัปโหลด ① รายงานภาษีขาย + ② GL",hint_need_one_more:"อัปโหลดอีก 1 ไฟล์",hint_ready:"พร้อมแล้ว · กดเริ่มกระทบยอด",hist_load:"โหลด",hist_export:"ส่งออก",hist_delete:"ลบ",confirm_delete:"ยืนยันการลบงานนี้?",s_gl_total:"ยอดรวมตามบัญชีแยกประเภท",s_minus_gl_cr:"หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย",s_plus_gl_dr:"บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย",s_plus_vat_p:"บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท",s_minus_vat_n:"หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท",s_vat_total:"ยอดรวมตามรายงานภาษีขาย"},zh:{not_found:"未找到数据",running:"正在对账中...",error:"出错了",need_files:"请先选择两个文件",done:"完成",hint_need_both:"请上传① 销项税报告 + ② 总账 GL",hint_need_one_more:"还需上传 1 份文件",hint_ready:"已就绪 · 点击开始对账",hist_load:"加载",hist_export:"导出",hist_delete:"删除",confirm_delete:"确认删除此任务？",s_gl_total:"总账金额合计",s_minus_gl_cr:"减：销项税报告中未列的贷方记录",s_plus_gl_dr:"加：销项税报告中未列的借方记录",s_plus_vat_p:"加：总账中未列的销售记录",s_minus_vat_n:"减：总账中未列的贷项凭单(credit note)记录",s_vat_total:"销项税报告金额合计"},en:{not_found:"Not found",running:"Reconciling...",error:"Error",need_files:"Please select both files",done:"Done",hint_need_both:"Upload ① Output VAT report + ② GL file",hint_need_one_more:"1 more file required",hint_ready:"Ready · click Run to start",hist_load:"Load",hist_export:"Export",hist_delete:"Delete",confirm_delete:"Delete this task?",s_gl_total:"Total per General Ledger",s_minus_gl_cr:"Less: GL credits not in VAT Report",s_plus_gl_dr:"Add: GL debits not in VAT Report",s_plus_vat_p:"Add: Sales in VAT Report not in GL",s_minus_vat_n:"Less: Credit notes in VAT Report not in GL",s_vat_total:"Total per VAT Sales Report"},ja:{not_found:"データなし",running:"照合中…",error:"エラー",need_files:"両方のファイルを選択してください",done:"完了",hint_need_both:"① 売上税報告 + ② GL をアップロード",hint_need_one_more:"あと 1 ファイル必要",hint_ready:"準備完了 · 「開始」をクリック",hist_load:"読込",hist_export:"出力",hist_delete:"削除",confirm_delete:"このタスクを削除しますか?",s_gl_total:"総勘定元帳合計",s_minus_gl_cr:"減：売上税報告にないGL貸方記録",s_plus_gl_dr:"加：売上税報告にないGL借方記録",s_plus_vat_p:"加：GLにない売上記録",s_minus_vat_n:"減：GLにない赤伝記録",s_vat_total:"売上税報告合計"}},r=E=>(i[a()]||i.th)[E]||E;function u(E){const g=a(),N={gl_no_revenue_rows:{zh:"GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。",th:"ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่",en:"No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.",ja:"GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。"},gl_parse_failed:{zh:"GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。",th:"อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน",en:"Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.",ja:"GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。"},vat_no_rows:{zh:"销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。",th:"ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง",en:"No rows found in the sales-VAT report. Please check you uploaded the correct report.",ja:"売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。"},vat_parse_failed:{zh:"销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。",th:"อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF",en:"Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.",ja:"売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。"}}[E];return N?N[g]||N.th||N.en:r("error")||"Error"}const l=E=>E==null||isNaN(E)?"":Number(E).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});function d(E,g,q,N){const K=e(E),Z=e(g),le=e(q);if(!K||!Z||!le)return;const ie=V=>{if(!V||!V.length)return;const Q=Array.isArray(s[N])?s[N].slice():[],ee=new Set(Q.map(ne=>ne.name+"|"+ne.size));for(const ne of V){if(!ne)continue;const oe=ne.name+"|"+ne.size;ee.has(oe)||(Q.push(ne),ee.add(oe))}s[N]=Q,c(le,Q),f(),m(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()};K.addEventListener("click",()=>Z.click()),K.addEventListener("keydown",V=>{(V.key==="Enter"||V.key===" ")&&(V.preventDefault(),Z.click())}),Z.addEventListener("change",()=>{ie(Array.from(Z.files||[])),Z.value=""}),K.addEventListener("dragover",V=>{V.preventDefault(),K.classList.add("drag-over")}),K.addEventListener("dragleave",()=>K.classList.remove("drag-over")),K.addEventListener("drop",V=>{V.preventDefault(),K.classList.remove("drag-over");const Q=V.dataTransfer&&V.dataTransfer.files?Array.from(V.dataTransfer.files):[];ie(Q)})}function c(E,g){if(!E)return;if(!g||g.length===0){E.textContent="";return}const q=g.reduce((N,K)=>N+Math.round(K.size/1024),0);if(g.length===1)E.textContent=g[0].name+"  ("+q+" KB)";else{const N=window.t&&window.t("glv-files-count")||"{n} 个文件";E.textContent=N.replace("{n}",g.length)+"  ("+q+" KB)"}}function p(E){const g=s[E];return Array.isArray(g)?g:g?[g]:[]}function f(){const E=e("btn-glv-run");if(!E)return;const g=p("glFile").length>0&&p("vatFile").length>0;E.disabled=!g||s.running}function m(){const E=e("glv-status");if(!E||s.running)return;const g=p("vatFile").length,q=p("glFile").length;g===0&&q===0?(E.className="vex-action-info muted",E.innerHTML="<span>"+r("hint_need_both")+"</span>"):g>0&&q>0?(E.className="vex-action-info ok",E.innerHTML="<span>"+r("hint_ready")+"</span>"):(E.className="vex-action-info muted",E.innerHTML="<span>"+r("hint_need_one_more")+"</span>")}function b(E,g){const q=E==="vat"?"vatFile":"glFile",N=E==="vat"?"glv-vat-input":"glv-gl-input",K=E==="vat"?"glv-vat-name":"glv-gl-name",Z=p(q);g==null?s[q]=[]:s[q]=Z.filter((ie,V)=>V!==g);const le=e(N);le&&(le.value=""),c(e(K),p(q)),f(),m(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}window._glvRemoveFile=b;function M(){s.glFile=[],s.vatFile=[],s.currentTaskId=null,s.lastDetail=[],s.lastSummary=null;const E=e("glv-vat-input");E&&(E.value="");const g=e("glv-gl-input");g&&(g.value="");const q=e("glv-vat-name");q&&(q.textContent="");const N=e("glv-gl-name");N&&(N.textContent="");const K=e("glv-result");K&&(K.style.display="none");const Z=e("glv-kpi-strip");Z&&(Z.style.display="none"),f(),m(),window._glvClearPreviewSearch&&window._glvClearPreviewSearch(),window._reconCollapse&&window._reconCollapse.renderGlvPreview&&window._reconCollapse.renderGlvPreview()}function I(E){const g=e("glv-tbody");if(!g)return;re(E.length),g.innerHTML="";const q=r("not_found"),N=document.createDocumentFragment();E.forEach(K=>{const Z=document.createElement("tr"),le=(ne,oe)=>{const ue=document.createElement("td");return oe&&(ue.className=oe),ue.textContent=ne,ue},ie=K.gl_amount===null||K.gl_amount===void 0,V=K.diff;let Q="glv-num",ee="glv-num";ie?(ee+=" glv-cell-missing",Q+=" glv-cell-missing"):Math.abs(V||0)<.005?Q+=" glv-cell-ok":Q+=" glv-cell-diff",Z.appendChild(le(K.doc_no||"","glv-doc")),Z.appendChild(le(K.date||"","")),Z.appendChild(le(K.customer_name||"","")),Z.appendChild(le(l(K.vat_amount),"glv-num")),Z.appendChild(le(ie?q:l(K.gl_amount),ee)),Z.appendChild(le(ie?q:l(K.diff),Q)),Z.appendChild(le(K.account_codes||"","glv-doc")),N.appendChild(Z)}),g.appendChild(N)}function x(E){const g=e("glv-summary-table")&&e("glv-summary-table").querySelector("tbody");if(!g)return;g.innerHTML="",[{label:r("s_gl_total"),amount:E.gl_total,emph:!0,items:[],negate:!1},{label:r("s_minus_gl_cr"),amount:-(E.gl_only_credit||0),emph:!1,items:E.gl_only_credit_items||[],negate:!0},{label:r("s_plus_gl_dr"),amount:E.gl_only_debit||0,emph:!1,items:E.gl_only_debit_items||[],negate:!1},{label:r("s_plus_vat_p"),amount:E.vat_only_positive||0,emph:!1,items:E.vat_only_positive_items||[],negate:!1},{label:r("s_minus_vat_n"),amount:E.vat_only_negative||0,emph:!1,items:E.vat_only_negative_items||[],negate:!1},{label:r("s_vat_total"),amount:E.vat_total,emph:!0,items:[],negate:!1}].forEach(({label:N,amount:K,emph:Z,items:le,negate:ie})=>{const V=document.createElement("tr");V.className=Z?"glv-summary-total":"glv-summary-sect";const Q=document.createElement("td"),ee=document.createElement("td");Q.textContent=N,ee.textContent=Z?l(K):"",V.appendChild(Q),V.appendChild(ee),g.appendChild(V),(le||[]).forEach(ne=>{const oe=document.createElement("tr");oe.className="glv-summary-item";const ue=document.createElement("td"),k=document.createElement("td"),T=[ne.doc_no,ne.date,ne.name].filter(Boolean);ue.textContent="· "+T.join("  ·  ");const A=ie?-(ne.amount||0):ne.amount||0;k.textContent=l(A),oe.appendChild(ue),oe.appendChild(k),g.appendChild(oe)})})}function y(E){e("glv-kpi-matched")&&(e("glv-kpi-matched").textContent=E&&E.matched!=null?E.matched:"—"),e("glv-kpi-diff")&&(e("glv-kpi-diff").textContent=E&&E.diff!=null?E.diff:"—"),e("glv-kpi-unmatched")&&(e("glv-kpi-unmatched").textContent=E&&E.unmatched!=null?E.unmatched:"—")}function $(E){if(!E)return"";try{const g=new Date(E);if(isNaN(g.getTime()))return E;const q=N=>String(N).padStart(2,"0");return g.getFullYear()+"-"+q(g.getMonth()+1)+"-"+q(g.getDate())+" "+q(g.getHours())+":"+q(g.getMinutes())}catch{return E}}const C=10;var F=[],j=1;function _(){j=1,h();var E=((e("glv-hist-search")||{}).value||"").trim().toLowerCase();if(E){var g=e("glv-history-tbody");g&&g.querySelectorAll("tr").forEach(function(q){q.dataset.taskId&&(q.style.display=q.textContent.toLowerCase().indexOf(E)>=0?"":"none")})}}function h(){const E=e("glv-history-table-wrap"),g=e("glv-history-empty"),q=e("glv-history-tbody"),N=e("glv-history-pager"),K=e("glv-history-pager-info"),Z=e("glv-history-prev"),le=e("glv-history-next");if(!q)return;if(q.innerHTML="",!F.length){E&&(E.style.display="none"),g&&(g.style.display=""),N&&(N.style.display="none");return}E&&(E.style.display=""),g&&(g.style.display="none");const ie=Math.ceil(F.length/C);j>ie&&(j=ie);const V=(j-1)*C,Q=F.slice(V,V+C);N&&(N.style.display=F.length>C?"":"none",K&&(K.textContent=j+" / "+ie),Z&&(Z.disabled=j<=1),le&&(le.disabled=j>=ie)),Q.forEach(ne=>{const oe=document.createElement("tr");oe.dataset.taskId=ne.id;const ue=document.createElement("td");ue.textContent=$(ne.created_at);const k=document.createElement("td");k.className="glv-history-file",k.title=(ne.vat_filename||"")+" + "+(ne.gl_filename||""),k.textContent=(ne.vat_filename||"?")+" + "+(ne.gl_filename||"?");const T=document.createElement("td");T.className="glv-num",T.textContent=(ne.vat_row_count||0)+" / "+(ne.gl_row_count||0);const A=document.createElement("td");A.className="glv-num",A.textContent=ne.matched_count||0;const U=document.createElement("td");U.className="glv-num",U.textContent=ne.diff_count||0;const z=document.createElement("td");z.className="glv-num",z.textContent=ne.unmatched_count||0;const v=document.createElement("td");v.className="glv-history-actions";const R=(de,se,ce,ae)=>{const pe=document.createElement("button");return pe.type="button",ce&&(pe.className=ce),pe.title=se,pe.setAttribute("aria-label",se),pe.innerHTML=de,pe.onclick=ae,pe},O='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',J='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',X='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';v.appendChild(R(O,r("hist_load"),"",()=>S(ne.id))),v.appendChild(R(J,r("hist_export"),"",()=>D(ne.id))),v.appendChild(R(X,r("hist_delete"),"glv-del",()=>B(ne.id))),[ue,k,T,A,U,z,v].forEach(de=>oe.appendChild(de)),q.appendChild(oe)})}function w(){var E=e("glv-history-prev"),g=e("glv-history-next");E&&!E._glvBound&&(E._glvBound=!0,E.addEventListener("click",function(){j>1&&(j--,h())})),g&&!g._glvBound&&(g._glvBound=!0,g.addEventListener("click",function(){var q=Math.ceil(F.length/C);j<q&&(j++,h())}))}async function L(){try{const g=await(await fetch("/api/recon/gl-vat/tasks",{headers:o()})).json();F=g&&g.tasks||[],j=1,h(),w()}catch(E){console.error("[gl-vat] history load failed:",E)}}async function S(E){try{const q=await(await fetch("/api/recon/gl-vat/"+E,{headers:o()})).json();if(!q||!q.ok)throw new Error("load_failed");s.currentTaskId=E,s.lastDetail=q.detail||[],s.lastSummary=q.summary||{},y(q.stats||{}),I(s.lastDetail),x(s.lastSummary);const N=e("glv-result");N&&(N.style.display=""),W(),window.scrollTo({top:N?N.offsetTop-80:0,behavior:"smooth"})}catch(g){console.error("[gl-vat] load task failed:",g),alert(r("error")+": "+(g.message||g))}}async function D(E){try{const g="/api/recon/gl-vat/"+E+"/export?lang="+encodeURIComponent(a()),q=await fetch(g,{headers:o()});if(!q.ok)throw new Error("HTTP "+q.status);const N=await q.blob(),K=document.createElement("a");K.href=URL.createObjectURL(N),K.download="GL_VAT_recon_"+E+".xlsx",document.body.appendChild(K),K.click(),setTimeout(()=>{URL.revokeObjectURL(K.href),K.remove()},200)}catch(g){console.error("[gl-vat] exportTask failed:",g),typeof showToast=="function"&&showToast(r("error")+": "+(g.message||g),"error")}}async function B(E){let g;if(typeof window.showConfirm=="function"?g=await window.showConfirm(r("confirm_delete"),{danger:!0}):g=confirm(r("confirm_delete")),!!g)try{const q=await fetch("/api/recon/gl-vat/"+E,{method:"DELETE",headers:o()});if(!q.ok)throw new Error("HTTP "+q.status);L()}catch(q){console.error("[gl-vat] delete failed:",q),typeof showToast=="function"&&showToast(r("error")+": "+(q.message||q),"error")}}async function P(){if(!s.glFile||!s.vatFile){typeof showToast=="function"&&showToast(r("need_files"),"warn");return}s.running=!0,f();const E=e("glv-status"),g=e("glv-progress"),q=e("glv-progress-sub");E&&(E.className="vex-action-info muted",E.style.color="",E.innerHTML="<span>"+r("running")+"</span>"),g&&(g.style.display=""),q&&(q.textContent=(s.vatFile.name||"VAT")+" + "+(s.glFile.name||"GL"));const N=new FormData,K=p("vatFile"),Z=p("glFile");for(const ie of K)N.append("vat_files",ie,ie.name);for(const ie of Z)N.append("gl_files",ie,ie.name);const le=(e("glv-prefix")&&e("glv-prefix").value||"4").trim()||"4";N.append("revenue_prefix",le),N.append("lang",a());try{const ie=await fetch("/api/recon/gl-vat/submit",{method:"POST",headers:o(),body:N});let V=null;try{V=await ie.json()}catch{V=null}if(!ie.ok||!V||!V.ok||!V.job_id)throw new Error(V&&V.detail||V&&V.error||"HTTP "+ie.status);const Q=e("glv-progress-sub"),ee=await window._reconPollJob(V.job_id,n(),{onProgress:k=>{Q&&(Q.textContent=window._reconProgressText(k,a()))}});if(!ee||ee.status!=="done"||!ee.result_id)throw ee&&ee.status==="failed"&&ee.error_code?new Error(u(ee.error_code)):new Error(r("error")||"Error");const ne=await fetch("/api/recon/gl-vat/"+encodeURIComponent(ee.result_id),{headers:o()});let oe=null;try{oe=await ne.json()}catch{oe=null}if(!ne.ok||!oe||!oe.ok)throw new Error(oe&&oe.detail||oe&&oe.error||"HTTP "+ne.status);s.currentTaskId=oe.task_id,s.lastDetail=oe.detail||[],s.lastSummary=oe.summary||{},y(oe.stats||{}),I(s.lastDetail),x(s.lastSummary);const ue=e("glv-result");ue&&(ue.style.display=""),W(),E&&(E.className="vex-action-info ok",E.style.color="",E.innerHTML="<span>"+r("done")+" · GL "+(oe.gl_row_count||0)+" · VAT "+(oe.vat_row_count||0)+"</span>"),L()}catch(ie){console.error("[gl-vat] run failed:",ie),E&&(E.className="vex-action-info",E.style.color="#ef4444",E.innerHTML="<span>"+r("error")+": "+(ie.message||ie)+"</span>")}finally{s.running=!1,g&&(g.style.display="none"),f()}}async function Y(){if(s.currentTaskId)try{const E="/api/recon/gl-vat/"+s.currentTaskId+"/export?lang="+encodeURIComponent(a()),g=await fetch(E,{headers:o()});if(!g.ok)throw new Error("HTTP "+g.status);const q=await g.blob(),N=document.createElement("a");N.href=URL.createObjectURL(q),N.download="GL_VAT_recon_"+s.currentTaskId+".xlsx",document.body.appendChild(N),N.click(),setTimeout(()=>{URL.revokeObjectURL(N.href),N.remove()},200)}catch(E){console.error("[gl-vat] export failed:",E),typeof showToast=="function"&&showToast(r("error")+": "+(E.message||E),"error")}}function G(){s.running||m(),L(),s.lastDetail&&s.lastDetail.length&&I(s.lastDetail),s.lastSummary&&x(s.lastSummary)}function W(){var E=e("glv-kpi-strip");E&&(E.style.display="");var g=e("glv-section-summary");g&&g.setAttribute("data-collapsed","false");var q=e("glv-section-detail");q&&q.setAttribute("data-collapsed","false")}function te(){document.querySelectorAll(".glv-section-head[data-toggle]").forEach(E=>{const g=E.getAttribute("data-toggle"),q=document.getElementById(g);if(!q)return;const N=K=>{if(K.target&&K.target.closest("button")!==null&&!K.target.classList.contains("glv-section-head"))return;const Z=q.getAttribute("data-collapsed")==="true";q.setAttribute("data-collapsed",Z?"false":"true")};E.addEventListener("click",N),E.addEventListener("keydown",K=>{(K.key==="Enter"||K.key===" ")&&(K.preventDefault(),N(K))})})}function re(E){const g=e("glv-detail-count");g&&(g.textContent=E!=null?String(E):"")}function H(){if(s.inited){L();return}s.inited=!0,d("glv-drop-gl","glv-gl-input","glv-gl-name","glFile"),d("glv-drop-vat","glv-vat-input","glv-vat-name","vatFile");const E=e("btn-glv-run");E&&E.addEventListener("click",P);const g=e("btn-glv-export");g&&g.addEventListener("click",Y);const q=e("btn-glv-reset");q&&q.addEventListener("click",M);const N=e("glv-hist-search");N&&N.addEventListener("input",_),te(),y(null),m(),window._loadGlvHistory=L,L(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("gl-vat-recon",G)}window.GlVatRecon={ensureInit:H},window._glvPreviewFiles=function(E){return p(E==="vat"?"vatFile":"glFile")}})();(function(){const e=["flowaccount","peak","xero","quickbooks","express"],n={flowaccount:"FlowAccount",peak:"PEAK",xero:"Xero",quickbooks:"QuickBooks",express:"Express"},a=["expense_office","expense_travel","expense_utility","asset_inventory","asset_fixed","liability_ap","revenue_sales","revenue_service","other"],o=["vat_7","vat_0","vat_exempt","wht_1","wht_3","wht_5","non_vat"],s="468b50c1-5593-4fd6-990d-515ce8085563";let i={sub:"clients",loaded:{clients:!1,accounts:!1,taxes:!1,products:!1},items:{clients:[],accounts:[],taxes:[],products:[]},clientList:[],clientLoaded:!1,addingNew:{clients:!1,accounts:!1,taxes:!1,products:!1},bound:!1};function r(){const S=typeof _userInfo<"u"?_userInfo:null;return!!(S&&(S.role==="owner"||S.is_super_admin))}function u(){const S=typeof _userInfo<"u"?_userInfo:null;return!!(S&&S.id===s)}function l(S){return typeof escapeHtml=="function"?escapeHtml(S==null?"":String(S)):String(S??"")}function d(S,D){try{typeof showToast=="function"&&showToast(S,D||"info")}catch{}}async function c(S,D){const B=localStorage.getItem("mrpilot_token");if(B&&!(i.loaded[S]&&!D))try{const P=await fetch("/api/erp/mappings/"+S,{headers:{Authorization:"Bearer "+B}});if(!P.ok)throw new Error("http_"+P.status);const Y=await P.json();i.items[S]=Y.items||[],i.loaded[S]=!0}catch{i.items[S]=[],i.loaded[S]=!1}}async function p(S){if(i.clientLoaded)return;const D=localStorage.getItem("mrpilot_token");if(D)try{const B=await fetch("/api/clients?include_inactive=false",{headers:{Authorization:"Bearer "+D}});if(!B.ok)throw new Error("http_"+B.status);const P=await B.json();i.clientList=(P.clients||P.items||[]).filter(Y=>Y.is_active!==!1),i.clientLoaded=!0}catch{i.clientList=[]}}function f(){const S=document.getElementById("erp-map-pane-wrap");if(!S)return;const D=!r();let B="";D&&(B+='<div class="erp-map-readonly-banner"><svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>'+l(t("erp-map-readonly-tip"))+"</div>"),B+='<div class="erp-map-toolbar">',!D&&i.sub!=="products"&&(B+='<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">'+l(t("erp-map-add-row"))+"</button>"),B+="</div>",B+='<div class="erp-map-table" id="erp-map-table-host"></div>',S.innerHTML=B,m();const P=document.getElementById("erp-map-dev-bar");P&&(P.style.display=r()&&u()?"":"none")}function m(){const S=document.getElementById("erp-map-table-host");if(!S)return;const D=i.sub,B=i.items[D]||[],P=i.addingNew[D],Y=!r();if(!B.length&&!P){S.innerHTML='<div class="erp-map-empty"><strong>'+l(t("erp-map-empty-"+D))+"</strong>"+l(t("erp-map-empty-"+D+"-sub"))+"</div>";return}let G="";G+=b(D),P&&!Y&&(G+=$(D)),B.forEach(function(W){G+=C(D,W,Y)}),S.innerHTML=G}function b(S){return S==="clients"?'<div class="erp-map-row erp-map-head row-clients"><div>'+l(t("erp-map-col-client"))+"</div><div>"+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":S==="accounts"?'<div class="erp-map-row erp-map-head row-accounts"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-category"))+"</div><div>"+l(t("erp-map-col-erp-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":S==="products"?'<div class="erp-map-row erp-map-head row-products"><div>'+l(t("erp-map-col-item-name"))+"</div><div>"+l(t("erp-map-col-erp-product-code"))+"</div><div>"+l(t("erp-map-col-erp-name"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>":'<div class="erp-map-row erp-map-head row-taxes"><div>'+l(t("erp-map-col-erp"))+"</div><div>"+l(t("erp-map-col-tax"))+"</div><div>"+l(t("erp-map-col-erp-tax-code"))+"</div><div>"+l(t("erp-map-col-notes"))+"</div><div>"+l(t("erp-map-col-actions"))+"</div></div>"}function M(S,D){let B='<select class="form-input" data-erp-field="'+D+'">';return B+='<option value="">'+l(t("erp-map-pick-erp"))+"</option>",e.forEach(function(P){const Y=P===S?" selected":"";B+='<option value="'+P+'"'+Y+">"+l(n[P])+"</option>"}),B+="</select>",B}function I(S){let D='<select class="form-input" data-erp-field="client_id">';return D+='<option value="">'+l(t("erp-map-pick-client"))+"</option>",(i.clientList||[]).forEach(function(B){const P=String(B.id)===String(S)?" selected":"";D+='<option value="'+B.id+'"'+P+">"+l(B.name||"#"+B.id)+"</option>"}),D+="</select>",D}function x(S){let D='<select class="form-input" data-erp-field="pearnly_category">';return D+='<option value="">'+l(t("erp-map-pick-cat"))+"</option>",a.forEach(function(B){const P=B===S?" selected":"";D+='<option value="'+B+'"'+P+">"+l(t("erp-map-cat-"+B))+"</option>"}),D+="</select>",D}function y(S){let D='<select class="form-input" data-erp-field="pearnly_tax_kind">';return D+='<option value="">'+l(t("erp-map-pick-tax"))+"</option>",o.forEach(function(B){const P=B===S?" selected":"";D+='<option value="'+B+'"'+P+">"+l(t("erp-map-tax-"+B))+"</option>"}),D+="</select>",D}function $(S){const D='<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">'+l(t("erp-map-save"))+"</button>";return S==="clients"?'<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new"><div data-label="'+l(t("erp-map-col-client"))+'">'+I("")+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+M("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-erp-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+D+"</div></div>":S==="accounts"?'<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+M("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-category"))+'">'+x("")+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-acc-code"))+'"></div><div data-label="'+l(t("erp-map-col-erp-name"))+'"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="'+l(t("erp-map-ph-acc-name"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+D+"</div></div>":'<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new"><div data-label="'+l(t("erp-map-col-erp"))+'">'+M("","erp_type")+'</div><div data-label="'+l(t("erp-map-col-tax"))+'">'+y("")+'</div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="'+l(t("erp-map-ph-tax-code"))+'"></div><div data-label="'+l(t("erp-map-col-notes"))+'"><input type="text" class="form-input" data-erp-field="notes" placeholder="'+l(t("erp-map-ph-notes"))+'"></div><div>'+D+"</div></div>"}function C(S,D,B){const P=B?"":'<button class="erp-map-del-btn" type="button" data-erp-del="'+l(D.id)+'" title="'+l(t("erp-map-delete"))+'"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg></button>',Y='<span class="erp-map-erp-badge">'+l(n[D.erp_type]||D.erp_type)+"</span>";if(S==="clients")return'<div class="erp-map-row row-clients"><div data-label="'+l(t("erp-map-col-client"))+'" class="erp-map-cell-name">'+l(D.client_name||"#"+D.client_id)+'</div><div data-label="'+l(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(D.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(D.notes||"")+"</div><div>"+P+"</div></div>";if(S==="accounts"){const W=t("erp-map-cat-"+(D.pearnly_category||"other"))||D.pearnly_category;return'<div class="erp-map-row row-accounts"><div data-label="'+l(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+l(t("erp-map-col-category"))+'" class="erp-map-cell-name">'+l(W)+'</div><div data-label="'+l(t("erp-map-col-erp-code"))+'" class="erp-map-code">'+l(D.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(D.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(D.notes||"")+"</div><div>"+P+"</div></div>"}if(S==="products")return'<div class="erp-map-row row-products"><div data-label="'+l(t("erp-map-col-item-name"))+'" class="erp-map-cell-name">'+l(D.item_name||"")+'</div><div data-label="'+l(t("erp-map-col-erp-product-code"))+'" class="erp-map-code">'+l(D.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-erp-name"))+'">'+l(D.erp_name||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(D.notes||"")+"</div><div>"+P+"</div></div>";const G=t("erp-map-tax-"+(D.pearnly_tax_kind||""))||D.pearnly_tax_kind;return'<div class="erp-map-row row-taxes"><div data-label="'+l(t("erp-map-col-erp"))+'">'+Y+'</div><div data-label="'+l(t("erp-map-col-tax"))+'" class="erp-map-cell-name"><span class="erp-map-tax-badge">'+l(G)+'</span></div><div data-label="'+l(t("erp-map-col-erp-tax-code"))+'" class="erp-map-code">'+l(D.erp_code||"")+'</div><div data-label="'+l(t("erp-map-col-notes"))+'">'+l(D.notes||"")+"</div><div>"+P+"</div></div>"}async function F(S){const D=i.sub,B={};S.querySelectorAll("[data-erp-field]").forEach(function(W){B[W.dataset.erpField]=(W.value||"").trim()});const P=localStorage.getItem("mrpilot_token");if(!P)return;let Y={},G="/api/erp/mappings/"+D;if(D==="clients"){if(!B.client_id||!B.erp_type||!B.erp_code){d(t("erp-map-save-fail"),"error");return}Y={client_id:parseInt(B.client_id,10),erp_type:B.erp_type,erp_code:B.erp_code,notes:B.notes||""}}else if(D==="accounts"){if(!B.erp_type||!B.pearnly_category||!B.erp_code){d(t("erp-map-save-fail"),"error");return}Y={erp_type:B.erp_type,pearnly_category:B.pearnly_category,erp_code:B.erp_code,erp_name:B.erp_name||"",notes:B.notes||""}}else{if(!B.erp_type||!B.pearnly_tax_kind||!B.erp_code){d(t("erp-map-save-fail"),"error");return}Y={erp_type:B.erp_type,pearnly_tax_kind:B.pearnly_tax_kind,erp_code:B.erp_code,notes:B.notes||""}}try{const W=await fetch(G,{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+P},body:JSON.stringify(Y)});if(!W.ok)throw new Error("http_"+W.status);i.addingNew[D]=!1,await c(D,!0),m(),d(t("erp-map-saved-toast"),"success")}catch{d(t("erp-map-save-fail"),"error")}}async function j(S){if(!await window.pearnlyConfirm(t("erp-map-confirm-delete")))return;const B=i.sub,P=localStorage.getItem("mrpilot_token");try{const Y=await fetch("/api/erp/mappings/"+B+"/"+encodeURIComponent(S),{method:"DELETE",headers:{Authorization:"Bearer "+P}});if(!Y.ok)throw new Error("http_"+Y.status);await c(B,!0),m(),d(t("erp-map-deleted-toast"),"success")}catch{d(t("erp-map-delete-fail"),"error")}}async function _(){await p(),await c(i.sub,!1),f()}function h(S){S!==i.sub&&(i.sub=S,i.addingNew[S]=!1,["clients","accounts","taxes","products"].forEach(function(D){D!==S&&(i.addingNew[D]=!1)}),document.querySelectorAll(".erp-map-subtab").forEach(function(D){D.classList.toggle("active",D.dataset.erpSubtab===S)}),c(S,!1).then(function(){f()}))}function w(){i.bound||(i.bound=!0,document.addEventListener("click",function(S){const D=S.target.closest(".erp-subtab[data-erp-subtab]");if(D){S.preventDefault();const W=D.dataset.erpSubtab;document.querySelectorAll(".erp-subtab").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubtab===W)}),document.querySelectorAll(".erp-subpanel").forEach(function(te){te.classList.toggle("active",te.dataset.erpSubpanel===W)}),W==="mappings"&&setTimeout(_,50);return}const B=S.target.closest(".erp-map-subtab[data-erp-subtab]");if(B){S.preventDefault(),h(B.dataset.erpSubtab);return}if(S.target.closest("#erp-map-add-btn")){if(S.preventDefault(),!r())return;i.addingNew[i.sub]=!0,m();return}const Y=S.target.closest('[data-erp-save="new"]');if(Y){S.preventDefault();const W=Y.closest('[data-erp-row="new"]');W&&F(W);return}const G=S.target.closest("[data-erp-del]");if(G){S.preventDefault(),j(G.dataset.erpDel);return}}))}function L(){const S=document.getElementById("erp-map-pane-wrap");S&&S.children.length>0&&f(),document.querySelectorAll(".erp-map-subtab").forEach(function(D){const B="erp-map-subtab-"+D.dataset.erpSubtab,P=t(B);P&&P!==B&&(D.textContent=P)})}w(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-mappings",L)})();(function(){let e=null,n=0,a=!1;function o(_){return typeof escapeHtml=="function"?escapeHtml(_==null?"":String(_)):String(_??"")}function s(_,h){try{typeof showToast=="function"&&showToast(_,h||"info")}catch{}}async function i(_){const h=Date.now();if(e&&h-n<3e4)return e;const w=localStorage.getItem("mrpilot_token");if(!w)return[];try{const L=await fetch("/api/erp/connectors/status",{headers:{Authorization:"Bearer "+w}});if(!L.ok)return[];const S=await L.json();return e=S&&S.connectors||[],n=h,e}catch{return[]}}function r(){try{return localStorage.getItem("pn_push_default_connector")||""}catch{return""}}function u(_){try{localStorage.setItem("pn_push_default_connector",_||"")}catch{}}function l(_){if(!_||!_.length)return null;const h=r();if(h){const L=_.find(S=>S.id===h);if(L)return L}const w=_.find(L=>L.is_default);return w||_[0]}function d(_){if(!_)return!1;const h=String(_.status||"").toLowerCase();return h==="exception"||h==="exception_pending"||h==="rejected"}function c(){try{return(typeof _results<"u"?_results:[])[typeof _drawerIdx<"u"?_drawerIdx:-1]||null}catch{return null}}function p(_){const h=_&&(_.type||_.id);return h==="xero"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M5.5 8l2 2 3-3.5"/></svg>':h==="webhook"?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="11.5" r="1.8"/><circle cx="11" cy="4.5" r="1.8"/><path d="M6.4 10l3.2-4M5 9.6V5.5a3 3 0 016 0"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/><rect x="11" y="3" width="3" height="10" rx="1"/></svg>'}async function f(_,h){if(!_||!h)return!1;const w=document.getElementById("btn-push-default");w&&(w.disabled=!0,w.classList.add("loading"));const L=localStorage.getItem("mrpilot_token");try{let S,D={method:"POST",headers:{Authorization:"Bearer "+L}};_.type==="xero"?S="/api/erp/xero/push/"+encodeURIComponent(h):(S="/api/erp/push",D.headers["Content-Type"]="application/json",D.body=JSON.stringify({history_id:h,endpoint_id:_.endpoint_id||void 0}));const B=await fetch(S,D);let P={};try{P=await B.json()}catch{}if(!B.ok){let Y=P&&P.detail||"unknown";typeof Y=="object"&&(Y=Y.code||JSON.stringify(Y));let G=String(Y||"unknown");if(_.type==="xero"){const W=G.replace(/^xero\./,"").toLowerCase(),te=t("xero-"+W);te&&te!=="xero-"+W&&(G=te)}return s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",G),"error"),!1}if(P&&P.ok===!1){let Y=P.error_msg||P.error_code||"unknown";return Y=String(Y).slice(0,200),s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",Y),"error"),!1}return s(t("unified-push-ok").replace("{name}",_.name),"success"),!0}catch(S){return s(t("unified-push-fail").replace("{name}",_.name).replace("{err}",S.message||"network"),"error"),!1}finally{w&&(w.disabled=!1,w.classList.remove("loading"))}}async function m(_,h){for(const w of _)await f(w,h)}function b(_,h){const w=document.createElement("div");w.className="pn-push-dropdown",w.id="pn-push-dropdown";const L=(_||[]).map(D=>{const B=!!(h&&D.id===h.id),P=D.method==="download"?t("unified-push-tag-download"):B?t("unified-push-tag-default"):"";return'<div class="pn-pd-item" data-cid="'+o(D.id)+'"><span class="pn-pd-icon">'+p(D)+'</span><span class="pn-pd-name">'+o(D.name)+"</span>"+(P?'<span class="pn-pd-tag">'+o(P)+"</span>":"")+(B?'<span class="pn-pd-check">✓</span>':"")+"</div>"}).join(""),S=_&&_.length>1?'<div class="pn-pd-divider"></div><div class="pn-pd-item pn-pd-all" data-cid="__all__"><span class="pn-pd-icon"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h10M3 10h10M3 13.5h6"/></svg></span><span class="pn-pd-name">'+o(t("unified-push-all").replace("{n}",_.length))+"</span></div>":"";return w.innerHTML=L+S,w}function M(){const _=document.getElementById("pn-push-dropdown");_&&_.remove()}async function I(){if(document.getElementById("pn-push-dropdown")){M();return}const _=await i()||[],h=l(_),w=b(_,h),L=document.getElementById("pn-push-wrap");L&&L.appendChild(w)}async function x(){const _=await i()||[],h=l(_);if(!h)return;const w=c(),L=w&&(w._historyId||w.history_id);if(L){if(d(w)){s(t("unified-push-disabled-exc"),"warn");return}await f(h,L)}}async function y(_){M();const h=await i()||[],w=c(),L=w&&(w._historyId||w.history_id);if(!L)return;if(d(w)){s(t("unified-push-disabled-exc"),"warn");return}if(_==="__all__"){await m(h,L);return}const S=h.find(D=>D.id===_);S&&(u(_),await f(S,L),C())}async function $(){const _=document.getElementById("drawer-history-save");if(!_||_.querySelector("#pn-push-wrap"))return;const h=document.createElement("div");h.id="pn-push-wrap",h.className="pn-push-wrap",h.dataset.loading="1",_.insertBefore(h,_.firstChild),["btn-push-erp","btn-xero-push"].forEach(P=>{_.querySelectorAll("#"+P).forEach(Y=>{Y.style.display="none"})});const w=await i()||[],L=l(w),S=w.length>0;if(!S)h.innerHTML='<button type="button" class="btn btn-ghost pn-push-empty" id="btn-push-default" disabled title="'+o(t("unified-push-empty-tip"))+'"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8h9M8 5l3 3-3 3"/></svg><span style="margin-left:4px;">'+o(t("unified-push-empty"))+"</span></button>";else{const P=w.length>1;h.innerHTML='<div class="pn-push-split"><button type="button" class="pn-push-main" id="btn-push-default" title="'+o(t("unified-push-tip"))+'">'+p(L)+"<span>"+o(t("unified-push-to").replace("{name}",L?L.name:""))+"</span></button>"+(P?'<button type="button" class="pn-push-arrow" id="btn-push-arrow" title="'+o(t("unified-push-other"))+'"><svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5l3 3 3-3"/></svg></button>':"")+"</div>"}delete h.dataset.loading;const D=h.querySelector("#btn-push-default");D&&S&&D.addEventListener("click",x);const B=h.querySelector("#btn-push-arrow");B&&B.addEventListener("click",function(P){P.stopPropagation(),I()}),a||(a=!0,document.addEventListener("click",function(P){const Y=P.target.closest(".pn-pd-item");if(Y){const G=Y.getAttribute("data-cid");y(G);return}P.target.closest("#btn-push-arrow")||M()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("unified-push",C))}function C(){const _=document.getElementById("pn-push-wrap");_&&(_.remove(),e=null,n=0,$())}function F(){const _=document.getElementById("drawer-history-save");if(!_||!_.querySelector("#pn-push-wrap"))return;["btn-push-erp","btn-xero-push"].forEach(w=>{_.querySelectorAll("#"+w).forEach(L=>{L.style.display!=="none"&&(L.style.display="none")})});const h=_.querySelectorAll("#pn-push-wrap");if(h.length>1)for(let w=1;w<h.length;w++)h[w].remove()}function j(){try{const _=function(){return document.getElementById("drawer-body")},h=new MutationObserver(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&$(),F()}),w=_();if(w)h.observe(w,{childList:!0,subtree:!0});else{const L=new MutationObserver(function(){const S=_();S&&(h.observe(S,{childList:!0,subtree:!0}),L.disconnect())});L.observe(document.body,{childList:!0,subtree:!0})}setTimeout(function(){document.getElementById("drawer-history-save")&&!document.getElementById("pn-push-wrap")&&$(),F()},200)}catch{}}j()})();(function(){function e(){const a=document.getElementById("erp-map-show-advanced-btn");if(!a)return;const o=document.getElementById("erp-map-subtabs");if(!o)return;const s=o.classList.contains("show-advanced"),i=a.querySelector(".erp-map-adv-btn-label");if(i&&typeof t=="function"){const r=s?"erp-map-hide-advanced":"erp-map-show-advanced",u=t(r);u&&u!==r&&(i.textContent=u)}a.setAttribute("aria-pressed",s?"true":"false")}document.addEventListener("click",function(a){if(!a.target.closest("#erp-map-show-advanced-btn"))return;a.preventDefault();const s=document.getElementById("erp-map-subtabs");if(s&&(s.classList.toggle("show-advanced"),e(),!s.classList.contains("show-advanced")&&s.querySelector(".erp-map-subtab.active.erp-map-subtab-advanced"))){const r=s.querySelector('.erp-map-subtab[data-erp-subtab="clients"]');r&&r.click()}});function n(){e()}typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-map-advanced-toggle",n)})();(function(){const e="pearnly_erp_onboard_shown";let n=!1;function a(){try{return Array.isArray(window._erpEndpoints)&&window._erpEndpoints.length>0}catch{return!1}}function o(){if(document.getElementById("erp-onboard-mask"))return;const i=document.createElement("div");i.id="erp-onboard-mask",i.className="erp-onboard-mask",i.innerHTML='<div class="erp-onboard-modal" role="dialog" aria-modal="true"><div class="erp-onboard-icon"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="6" width="24" height="20" rx="3"/><path d="M9 13h14M9 18h10"/><path d="M22 22l3 3 5-5"/></svg></div><div class="erp-onboard-title" id="erp-onboard-title"></div><div class="erp-onboard-body" id="erp-onboard-body"></div><div class="erp-onboard-btns"><button type="button" class="btn btn-secondary" id="erp-onboard-later"></button><button type="button" class="btn btn-primary" id="erp-onboard-ok"></button></div></div>',document.body.appendChild(i);function r(){const l=document.getElementById("erp-onboard-title"),d=document.getElementById("erp-onboard-body"),c=document.getElementById("erp-onboard-ok"),p=document.getElementById("erp-onboard-later");l&&(l.textContent=t("erp-onboard-title")),d&&(d.textContent=t("erp-onboard-body")),c&&(c.textContent=t("erp-onboard-ok")),p&&(p.textContent=t("erp-onboard-later"))}r();function u(){i.style.display="none"}document.getElementById("erp-onboard-ok").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}u();try{const l=document.querySelector('#btn-add-endpoint, [data-action="erp-add-endpoint"]');l&&l.scrollIntoView({behavior:"smooth",block:"center"})}catch{}}),document.getElementById("erp-onboard-later").addEventListener("click",function(){try{localStorage.setItem(e,"1")}catch{}u()}),i.addEventListener("click",function(l){l.target===i&&u()}),typeof window.subscribeI18n=="function"&&window.subscribeI18n("erp-onboard-modal",function(){i.style.display!=="none"&&r()})}function s(){if(!n){try{if(localStorage.getItem(e)==="1")return}catch{}a()||(n=!0,o(),requestAnimationFrame(function(){requestAnimationFrame(function(){if(a())return;const i=document.getElementById("erp-onboard-mask");i&&(i.style.display="flex")})}))}}document.addEventListener("click",function(i){const r=i.target.closest('.auto-nav-item[data-auto-tab="erp"]'),u=i.target.closest('.erp-subtab[data-erp-subtab="connect"]');(r||u)&&setTimeout(s,700)})})();(function(){const e={parse:{zh:"解析文件中",th:"กำลังอ่านไฟล์",en:"Parsing files",ja:"ファイル解析中"},report:{zh:"读取报告中",th:"กำลังอ่านรายงาน",en:"Reading report",ja:"レポート読込中"},reconcile:{zh:"对账中",th:"กำลังกระทบยอด",en:"Reconciling",ja:"照合中"},build:{zh:"生成中",th:"กำลังสร้างไฟล์",en:"Building",ja:"作成中"},persist:{zh:"保存中",th:"กำลังบันทึก",en:"Saving",ja:"保存中"},done:{zh:"完成",th:"เสร็จสิ้น",en:"Done",ja:"完了"}};window._reconProgressText=function(n,a){n=n||{},a=window._currentLang||a||localStorage.getItem("mrpilot_lang")||"th",e.parse[a]||(a="th");const o=n.stage||"parse",s=e[o]||e.parse,i=s[a]||s.th||s.en,r=n.stage_total,u=n.stage_done;if(o==="parse"&&Number.isFinite(r)&&r>0){const l={zh:"共 {d}/{t} 个文件",th:"{d}/{t} ไฟล์",en:"{d}/{t} files",ja:"{d}/{t} ファイル"}[a]||"{d}/{t} files";return i+" · "+l.replace("{d}",u||0).replace("{t}",r)}return i},window._reconPollJob=async function(n,a,o){o=o||{};const s=o.intervalMs||1500,i=o.maxMs||1200*1e3,r=Date.now();let u=0;for(;;){let l=null;try{const d=await fetch("/api/recon/jobs/"+encodeURIComponent(n),{headers:{Authorization:"Bearer "+a}});try{l=await d.json()}catch{l=null}(!d.ok||!l||!l.ok)&&(l=null)}catch{l=null}if(l){if(u=0,o.onProgress)try{o.onProgress(l.progress||{},l)}catch{}if(l.status==="done"||l.status==="failed"||l.status==="needs_review"||l.status==="needs_mapping")return l}else if(++u>=10)return{ok:!1,status:"failed",error_code:"poll_unreachable"};if(Date.now()-r>i)return{ok:!1,status:"timeout",error_code:"timeout"};await new Promise(d=>setTimeout(d,s))}}})();(function(){let e=!1,n=[],a=[],o=null,s="all",i=[],r={stmt:"",gl:""},u=[];const l=k=>document.getElementById(k);function d(k){if(k==null)return"—";const T=Number(k);return isNaN(T)?"—":T.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2})}function c(k){return k?String(k).slice(0,10).split("-").reverse().join("/"):"—"}function p(k){return String(k||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}function f(k,T){T=window._currentLang||T||"th";const A={stmt_headers_not_found:{zh:"认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV",ja:"銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传",th:"หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่",en:"Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV",ja:"GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า",en:"No transaction rows found · please upload the correct statement, or try a clearer version",ja:"取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください"},no_rows:{zh:"解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传",th:"ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่",en:"No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version",ja:"解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel",en:"File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel",ja:"ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV",en:"Could not read the file · try a clearer version, or convert to PDF / Excel / CSV",ja:"読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください"}},U={zh:"解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传",th:"อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่",en:"Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload",ja:"解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください"},z=A[k]||U;return z[T]||z.th||z.en}function m(k){const T=k==="stmt"?n:a,A=l(`brv2-${k}-name`);if(A)if(T.length===0)A.textContent="";else{const z=window._currentLang||"zh",v={zh:"个文件",th:" ไฟล์",en:" file(s)",ja:" ファイル"};A.textContent=T.length+(v[z]||" 个文件")}const U=l("brv2-preview-panel");U&&U.style.display!=="none"&&I(k),b()}function b(){const k=l("brv2-toggle-preview"),T=l("brv2-preview-panel"),A=n.length+a.length>0;k&&(k.style.display=A?"":"none"),!A&&T&&(T.style.display="none",k&&k.classList.remove("open"))}function M(){I("stmt"),I("gl")}function I(k){const T=l(k==="stmt"?"brv2-pp-stmt-col":"brv2-pp-gl-col");if(!T)return;const A=k==="stmt"?n:a,U=window._currentLang||"zh",z={stmt:{zh:"① 银行账单",th:"① บัญชีธนาคาร",en:"① Bank Stmt",ja:"① 銀行明細"},gl:{zh:"② 总账 GL",th:"② GL รายงาน",en:"② GL Report",ja:"② GL帳簿"}},v=(z[k]||{})[U]||z[k].zh,R=p(window.t&&window.t("vex-preview-search")||"搜索文件名..."),O=p(window.t&&window.t("vex-preview-clear-all")||"全清"),J=r[k]||"";T.innerHTML='<div class="vex-pp-col-title"><span class="vex-pp-col-name">'+p(v)+' <span class="vex-pp-col-count">'+A.length+'</span></span></div><div class="vex-pp-search-row"><input class="vex-pp-search" id="brv2-pp-search-'+k+'" type="text" placeholder="'+R+'" value="'+p(J)+'" autocomplete="off"><button class="vex-pp-clear-btn" id="brv2-pp-clearall-'+k+'" type="button">'+O+'</button></div><div class="vex-pp-file-list" id="brv2-pp-'+k+'-list"></div><div class="vex-pp-pagination" id="brv2-pp-'+k+'-pg"></div>';const X=l("brv2-pp-search-"+k);X&&X.addEventListener("input",function(se){r[k]=se.target.value,x(k)});const de=l("brv2-pp-clearall-"+k);de&&de.addEventListener("click",function(){k==="stmt"?n.length=0:a.length=0,m(k),P()}),x(k)}function x(k){const T=l("brv2-pp-"+k+"-list"),A=l("brv2-pp-"+k+"-pg");if(!T)return;const U=k==="stmt"?n:a,z=(r[k]||"").toLowerCase(),v=z?U.filter(J=>J.name.toLowerCase().includes(z)):U.slice(),R='<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>',O='<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';if(T.innerHTML=v.map((J,X)=>'<div class="vex-pp-file-row">'+R+'<span class="vex-pp-fi-name" title="'+p(J.name)+'">'+p(J.name)+'</span><span class="vex-pp-fi-size">'+y(J.size)+'</span><button class="vex-pp-fi-del" type="button" data-zone="'+k+'" data-idx="'+U.indexOf(J)+'" aria-label="remove">'+O+"</button></div>").join(""),T.querySelectorAll(".vex-pp-fi-del").forEach(function(J){J.addEventListener("click",function(){const X=parseInt(J.dataset.idx,10);J.dataset.zone==="stmt"?n.splice(X,1):a.splice(X,1),m(J.dataset.zone),P()})}),A){const J=window.t&&window.t("vex-preview-count")||"显示 {n} / 共 {m}";A.textContent=J.replace("{n}",v.length).replace("{m}",U.length)}}function y(k){return k?k<1024?k+" B":k<1048576?(k/1024).toFixed(1)+" KB":(k/1048576).toFixed(1)+" MB":""}var $="pearnly.brv2.lastAnchorOcr";function C(k){try{var T=k&&k._anchor_ocr;if(!T||typeof T!="object")return;var A={stmt_opening:Number.isFinite(+T.stmt_opening)?+T.stmt_opening:null,gl_opening:Number.isFinite(+T.gl_opening)?+T.gl_opening:null,gl_closing:Number.isFinite(+T.gl_closing)?+T.gl_closing:null,stmt_closing:Number.isFinite(+T.stmt_closing)?+T.stmt_closing:null,ts:Date.now()};localStorage.setItem($,JSON.stringify(A))}catch{}}function F(){try{var k=localStorage.getItem($);if(!k)return null;var T=JSON.parse(k);return!T||typeof T!="object"?null:T}catch{return null}}function j(){var k=F();if(k){var T={"brv2-anchor-stmt-opening":k.stmt_opening,"brv2-anchor-gl-opening":k.gl_opening,"brv2-anchor-gl-closing":k.gl_closing,"brv2-anchor-stmt-closing":k.stmt_closing},A=0;Object.keys(T).forEach(function(O){var J=document.getElementById(O);if(J&&J.value===""){var X=T[O];if(Number.isFinite(X)){J.value=X.toFixed(2);var de=J.closest&&J.closest(".brv2-anchor-cell");de&&de.classList.add("is-prefilled"),A+=1}}});var U=document.getElementById("brv2-anchor-eq"),z=document.getElementById("brv2-anchor-eq-val");if(U&&z&&Number.isFinite(k.stmt_opening)&&Number.isFinite(k.gl_opening)){var v=k.stmt_opening-k.gl_opening;z.textContent=v.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),U.style.display=""}if(A>0){var R=document.getElementById("brv2-anchor-prefill-banner");R&&R.classList.add("show")}}}function _(){var k=document.getElementById("brv2-anchor-prefill-banner");if(k){var T=!1;["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"].forEach(function(A){var U=document.getElementById(A);if(U){var z=U.closest&&U.closest(".brv2-anchor-cell");z&&z.classList.contains("is-prefilled")&&(T=!0)}}),k.classList.toggle("show",T)}}var h=[["stmt_opening","brv2-anchor-stmt-opening"],["gl_opening","brv2-anchor-gl-opening"],["gl_closing","brv2-anchor-gl-closing"],["stmt_closing","brv2-anchor-stmt-closing"]];function w(k,T){return window.t&&window.t(k)||T}function L(k){return String(k??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function S(k){return Number.isFinite(+k)?(+k).toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}function D(k){var T=document.getElementById("brv2-summary-collapse");if(!(!T||!T.parentNode)){var A=document.getElementById("brv2-anchor-audit"),U=k&&k._anchor_overrides;if(!U||typeof U!="object"||Object.keys(U).length===0){A&&A.parentNode&&A.parentNode.removeChild(A);return}A||(A=document.createElement("div"),A.id="brv2-anchor-audit",A.style.cssText="margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px 16px;",T.parentNode.insertBefore(A,T.nextSibling));var z=h.map(function(v){var R=U[v[0]];if(!R)return"";var O=+R.ocr||0,J=+R.user||0,X=J-O,de=X>0?"+":(X<0,""),se=Math.abs(X)<.005?"#6b7280":X>0?"#16a34a":"#dc2626";return'<tr><td style="padding:6px 10px;color:#111827;font-size:13px">'+L(w(v[1],v[0]))+'</td><td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+L(S(O))+'</td><td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+L(S(J))+'</td><td style="padding:6px 10px;color:'+se+';font-weight:500;font-size:13px;text-align:right;font-variant-numeric:tabular-nums">'+L(de+S(X))+"</td></tr>"}).join("");A.innerHTML='<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">'+L(w("brv2-anchor-audit-title","⚠ This run contains manually entered anchors"))+'</div><table style="width:100%;border-collapse:collapse;font-family:inherit"><thead><tr><th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(w("brv2-anchor-audit-col-field","Field"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(w("brv2-anchor-audit-col-ocr","OCR"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(w("brv2-anchor-audit-col-user","User"))+'</th><th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;font-weight:500;border-bottom:1px solid #fed7aa">'+L(w("brv2-anchor-audit-col-diff","Diff"))+"</th></tr></thead><tbody>"+z+"</tbody></table>"}}function B(){const k=l("brv2-toggle-preview");k&&!k._reconBound&&(k._reconBound=!0,k.addEventListener("click",function(){const T=l("brv2-preview-panel"),A=l("brv2-toggle-preview-label"),U=T&&T.style.display!=="none";T&&(T.style.display=U?"none":""),k.classList.toggle("open",!U),A&&(A.textContent=U?window.t&&window.t("vex-toggle-preview-open")||"查看清单":window.t&&window.t("vex-toggle-preview-close")||"收起清单"),U||M()}))}function P(){const k=l("brv2-run-btn"),T=l("brv2-status"),A=n.length>0,U=a.length>0;if(k&&(k.disabled=!(A&&U)),T){const z=window._currentLang||"zh";if(!A&&!U){const v={zh:"请上传银行账单和 GL 文件",th:"กรุณาอัปโหลดบัญชีธนาคารและ GL",en:"Upload bank statement and GL files",ja:"銀行明細と GL を両方アップロードしてください"};T.textContent=v[z]||v.zh}else if(A)if(U){const v={zh:"两份文件已就绪",th:"พร้อมสอบทาน",en:"Ready to reconcile",ja:"照合を開始できます"};T.textContent=v[z]||v.zh}else{const v={zh:"还缺 GL 文件",th:"ยังขาดไฟล์ GL",en:"Missing GL file",ja:"GL ファイルが未アップロード"};T.textContent=v[z]||v.zh}else{const v={zh:"还缺银行账单 PDF",th:"ยังขาดไฟล์บัญชีธนาคาร PDF",en:"Missing bank statement PDF",ja:"銀行明細 PDF が未アップロード"};T.textContent=v[z]||v.zh}}}function Y(k,T,A){const U=l(k),z=l(T);!U||!z||(U.addEventListener("click",()=>z.click()),U.addEventListener("keydown",v=>{(v.key==="Enter"||v.key===" ")&&(v.preventDefault(),z.click())}),U.addEventListener("dragover",v=>{v.preventDefault(),U.classList.add("drag-over")}),U.addEventListener("dragleave",()=>U.classList.remove("drag-over")),U.addEventListener("drop",v=>{v.preventDefault(),U.classList.remove("drag-over");const R=Array.from(v.dataTransfer.files||[]);A==="stmt"?n.push(...R):a.push(...R),m(A),P()}),z.addEventListener("change",()=>{const v=Array.from(z.files||[]);A==="stmt"?n.push(...v):a.push(...v),z.value="",m(A),P()}))}function G(k){const T=l("brv2-progress"),A=l("brv2-run-btn"),U=l("brv2-error");T&&(T.style.display=k?"":"none"),A&&(A.disabled=k),U&&(U.style.display="none")}function W(k){const T=l("brv2-error");T&&(T.textContent=k,T.style.display="",T.scrollIntoView({behavior:"smooth",block:"nearest"})),G(!1),P(),window.showToast&&window.showToast(k,"error")}async function te(){if(n.length===0||a.length===0)return;const k=localStorage.getItem("mrpilot_token")||"",T=window._currentLang||"zh",A=(l("brv2-acct-select")||{}).value||"";H(!1),G(!0);try{const U=new FormData;n.forEach(ae=>U.append("stmt_files",ae)),a.forEach(ae=>U.append("gl_files",ae)),U.append("gl_account",A),U.append("lang",T);const z=parseFloat((l("brv2-anchor-gl-closing")||{}).value),v=parseFloat((l("brv2-anchor-stmt-closing")||{}).value),R=parseFloat((l("brv2-anchor-stmt-opening")||{}).value),O=parseFloat((l("brv2-anchor-gl-opening")||{}).value);Number.isFinite(z)&&U.append("gl_closing_override",z),Number.isFinite(v)&&U.append("stmt_closing_override",v),Number.isFinite(R)&&U.append("stmt_opening_override",R),Number.isFinite(O)&&U.append("gl_opening_override",O);const J=await fetch("/api/recon/bank-v2/submit",{method:"POST",headers:{Authorization:"Bearer "+k},body:U});let X=null;try{X=await J.json()}catch{X=null}if(X&&X.needs_mapping){G(!1),window.ReconMapping?window.ReconMapping.show(X,{token:k,lang:T,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(!J.ok||!X||!X.ok||!X.job_id){G(!1),X&&(X.detail||X.error)?W(_humanizeBackendError(X.detail||X.error,"Error "+J.status)):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const de=l("brv2-progress-sub"),se=await window._reconPollJob(X.job_id,k,{onProgress:ae=>{de&&(de.textContent=window._reconProgressText(ae,T))}});if(se&&se.status==="needs_mapping"&&se.mapping){G(!1),window.ReconMapping?window.ReconMapping.show(se.mapping,{token:k,lang:T,onConfirmed:function(){te()}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="needs_review"&&se.review){G(!1),window.ReconReview?window.ReconReview.show(se.review,{token:k,lang:T,jobId:X.job_id,onConfirmed:async function(ae){G(!0);const pe=await window._reconPollJob(ae,k,{onProgress:fe=>{de&&(de.textContent=window._reconProgressText(fe,T))}});await ce(pe)}}):W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}if(se&&se.status==="failed"){G(!1),W(f(se.error_code,T));return}await ce(se);async function ce(ae){try{if(!ae||ae.status!=="done"||!ae.result_id){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}const pe=await fetch("/api/recon/bank-v2/"+encodeURIComponent(ae.result_id),{headers:{Authorization:"Bearer "+k}});let fe=null;try{fe=await pe.json()}catch{fe=null}if(!pe.ok||fe===null||!fe.ok){G(!1),W(t("brv2-err-server")||"服务器繁忙,请稍后重试");return}(fe.gl_accounts||[]).length>1&&re(fe.gl_accounts),o=fe,i=fe.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(ge=>ge.classList.toggle("active",ge.dataset.filter==="all")),C(fe&&fe.summary),G(!1),N(fe),Z();const me=l("brv2-summary-collapse");me&&me.scrollIntoView({behavior:"smooth",block:"nearest"})}catch(pe){G(!1),W(pe.message||"Network error")}}}catch(U){W(U.message||"Network error")}}function re(k){const T=l("brv2-acct-select");if(!T)return;const A=window._currentLang||"zh",U={zh:"全部账户",th:"ทุกบัญชี",en:"All Accounts",ja:"すべての口座"}[A]||"全部账户";T.innerHTML=`<option value="">${U}</option>`+k.map(z=>`<option value="${p(z)}">${p(z)}</option>`).join(""),T.style.display=""}function H(k){const T=l("brv2-summary-collapse"),A=l("brv2-detail-collapse"),U=l("brv2-export-btn"),z=l("brv2-new-btn"),v=l("brv2-parse-info-wrap");T&&(T.style.display=k?"":"none"),A&&(A.style.display=k?"":"none"),U&&(U.style.display=k?"":"none"),z&&(z.style.display=k?"":"none"),!k&&v&&(v.style.display="none");const R=l("brv2-warnings");!k&&R&&(R.style.display="none",R.innerHTML="")}function E(k){const T=l("brv2-parse-info-wrap"),A=l("brv2-parse-info-body");if(!T||!A)return;const U=k.parse_info;if(!U){T.style.display="none";return}const z=window._currentLang||"zh",v={title:{zh:"文件解析状态",th:"สถานะการอ่านไฟล์",en:"File Parse Status",ja:"ファイル解析状態"},type:{zh:"类型",th:"ประเภท",en:"Type",ja:"種別"},file:{zh:"文件名",th:"ชื่อไฟล์",en:"File",ja:"ファイル"},rows:{zh:"解析行数",th:"แถวที่พบ",en:"Rows Found",ja:"解析行数"},bank:{zh:"银行/科目",th:"ธนาคาร/บัญชี",en:"Bank/Account",ja:"銀行/科目"},status:{zh:"状态",th:"สถานะ",en:"Status",ja:"状態"},stmt:{zh:"账单",th:"บัญชีธนาคาร",en:"Stmt",ja:"明細"},gl:{zh:"总账GL",th:"GL",en:"GL",ja:"GL"},ok:{zh:"✓ 成功",th:"✓ สำเร็จ",en:"✓ OK",ja:"✓ 成功"},warn:{zh:"⚠ 0行",th:"⚠ 0 แถว",en:"⚠ 0 rows",ja:"⚠ 0行"},fail:{zh:"✗ 失败",th:"✗ ล้มเหลว",en:"✗ Failed",ja:"✗ 失敗"}},R=ce=>(v[ce]||{})[z]||(v[ce]||{}).zh||ce,O=[...(U.stmt_files||[]).map(ce=>({...ce,_type:"stmt",_extra:ce.bank_code||""})),...(U.gl_files||[]).map(ce=>({...ce,_type:"gl",_extra:(ce.accounts||[]).join(", ")}))],J={stmt_headers_not_found:{zh:"认不出表头列 · 请确认文件含日期/金额/余额列",th:"หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ",en:"Cannot detect column headers · ensure file has date/amount/balance columns",ja:"列ヘッダーが認識できません · 日付/金額/残高列を確認してください"},stmt_no_rows:{zh:"文件里没有交易数据 · 请确认上传了正确的银行流水",th:"ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง",en:"No transaction rows found · please check the file",ja:"取引データが見つかりません · ファイルを確認してください"},file_not_supported:{zh:"不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV",th:"ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV",en:"File type not supported · please upload PDF / image / Excel / CSV",ja:"このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード"},file_unreadable:{zh:"文件无法读取 · 可能已损坏或被加密",th:"อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส",en:"File cannot be read · may be corrupted or encrypted",ja:"ファイルを読み取れません · 破損または暗号化の可能性"},ocr_failed:{zh:"文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传",th:"อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF",en:"Could not read file · try a clearer version or upload as PDF",ja:"読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行"},gl_headers_not_found:{zh:"认不出总账表头 · 请确认文件含科目/借方/贷方列",th:"หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต",en:"Cannot detect GL column headers · ensure account/debit/credit columns exist",ja:"GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください"}},X=ce=>{const ae=String(ce||"");return/Cannot detect bank statement column headers/i.test(ae)?"stmt_headers_not_found":/Cannot detect GL column headers/i.test(ae)?"gl_headers_not_found":/No transaction rows found|no pages parsed/i.test(ae)?"stmt_no_rows":/unsupported format/i.test(ae)?"file_not_supported":/Cannot read Excel|file_unreadable/i.test(ae)?"file_unreadable":/Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(ae)?"ocr_failed":null},de=ce=>{const ae=ce.error_code||X(ce.error);if(ae&&J[ae]){const pe=window._currentLang||"zh";return J[ae][pe]||J[ae].zh}return String(ce.error||"").slice(0,80)},se=ce=>!ce.ok&&ce.error?`<span style="color:#dc2626">${R("fail")} — ${p(de(ce))}</span>`:ce.rows?`<span style="color:#059669">${R("ok")} (${ce.rows})</span>`:`<span style="color:#d97706">${R("warn")}</span>`;A.innerHTML=`
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${R("title")}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${R("type")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${R("file")}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${R("rows")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${R("bank")}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${R("status")}</th>
                    </tr>
                </thead>
                <tbody>
                    ${O.map(ce=>`<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${ce._type==="stmt"?R("stmt"):R("gl")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${p(ce.file||"")}">${p(ce.file||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${ce.rows||0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${p(ce._extra||"")}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${se(ce)}</td>
                    </tr>`).join("")}
                </tbody>
            </table>`,T.style.display=""}async function g(k){const T=localStorage.getItem("mrpilot_token")||"",A=window._currentLang||"zh";try{const U=await fetch("/api/recon/bank-v2/"+k+"/export?lang="+A,{headers:{Authorization:"Bearer "+T}});if(!U.ok){const de=await U.json().catch(()=>({}));window.showToast&&window.showToast(de.detail||"Export failed","error");return}const z=await U.blob(),R=(U.headers.get("content-disposition")||"").match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/),O=R?R[1].replace(/['"]/g,""):"reconciliation.xlsx",J=URL.createObjectURL(z),X=document.createElement("a");X.href=J,X.download=O,document.body.appendChild(X),X.click(),document.body.removeChild(X),URL.revokeObjectURL(J)}catch(U){window.showToast&&window.showToast("Export error: "+U.message,"error")}}function q(k,T){const A=l("brv2-summary-collapse");let U=l("brv2-warnings");const z=window._currentLang||"zh",v={zh:"⏭ 已跳过无法识别的文件:",th:"⏭ ข้ามไฟล์ที่อ่านไม่ได้:",en:"⏭ Skipped unreadable file:",ja:"⏭ 読み取れないファイルをスキップ:"}[z]||"⏭ ",R=[];if((T||[]).forEach(O=>R.push(v+" "+O)),(k||[]).forEach(O=>R.push(O)),!R.length){U&&(U.style.display="none");return}if(!U)if(U=document.createElement("div"),U.id="brv2-warnings",A&&A.parentNode)A.parentNode.insertBefore(U,A);else return;U.style.cssText="display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6",U.innerHTML=R.map(O=>"<div>"+p(O)+"</div>").join("")}function N(k){E(k),q(k.warnings||[],k.skipped_files||[]),!k.ok&&k.error&&window.showToast&&window.showToast(k.error,"error");const T=k.stats||{},A=k.summary||{},U=T.matched||0,z=(T.gl_debit_only||0)+(T.gl_credit_only||0),v=(T.stmt_withdrawal_only||0)+(T.stmt_deposit_only||0),R=Number(A.formula_diff||0),O=Math.abs(R)<.05;l("brv2-kpi-matched")&&(l("brv2-kpi-matched").textContent=U),l("brv2-kpi-diff")&&(l("brv2-kpi-diff").textContent=d(R)),l("brv2-kpi-unmatched")&&(l("brv2-kpi-unmatched").textContent=z+v);const J=l("brv2-kpi-diff-icon");J&&(J.style.background=O?"#d1fae5":"#fee2e2",J.style.color=O?"#065f46":"#b91c1c");const X=l("brv2-formula-sub");if(X){const pe=window._currentLang||"zh";X.textContent=O?{zh:"✓ 平衡",th:"✓ สมดุล",en:"✓ Balanced",ja:"✓ 一致"}[pe]||"✓ 平衡":({zh:"差 ",th:"ต่าง ",en:"Diff ",ja:"差 "}[pe]||"差 ")+d(R)}const de=l("brv2-detail-sub");if(de){const pe=window._currentLang||"zh",fe={zh:"共 {n} 行",th:"ทั้งหมด {n} แถว",en:"{n} rows",ja:"計 {n} 行"}[pe]||"共 {n} 行";de.textContent=fe.replace("{n}",i.length)}function se(pe,fe,me){const ge=l(pe);ge&&(ge.textContent=(me&&fe>0?"(":"")+d(me?-fe:fe)+(me&&fe>0?")":""))}se("brf-gl-close",A.gl_closing||0),se("brf-open-diff",A.opening_diff||0),se("brf-gl-debit-only",A.gl_debit_only_amount||0,!0),se("brf-gl-credit-only",A.gl_credit_only_amount||0),se("brf-stmt-wd-only",A.stmt_withdrawal_only_amount||0,!0),se("brf-stmt-dep-only",A.stmt_deposit_only_amount||0),se("brf-calc-close",A.formula_stmt_closing||0),se("brf-stmt-close",A.stmt_closing||0),l("brf-diff")&&(l("brf-diff").textContent=d(R));const ce=l("brv2-fcell-diff");ce&&ce.classList.toggle("brv2-fcell-diff-ok",O);const ae=l("brv2-export-btn");ae&&(ae.onclick=()=>{o&&g(o.task_id)}),D(A),H(!0),K()}function K(){const k=l("brv2-tbody");if(!k)return;const T=i.filter(v=>s==="all"?!0:s==="matched"?v.match_status==="matched":s==="gl_only"?v.match_status.startsWith("gl_"):s==="stmt_only"?v.match_status.startsWith("stmt_"):!0);if(T.length===0){const v={zh:"无记录",th:"ไม่มีรายการ",en:"No rows",ja:"行なし"}[window._currentLang||"zh"]||"无记录";k.innerHTML=`<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${v}</td></tr>`;return}const A=window._currentLang||"zh",U={zh:"OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF",th:"การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ",en:"Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF",ja:"残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください"}[A],z={zh:"OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF",th:"OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ",en:"OCR low confidence · digit was blurry or hard to read — verify against the original PDF",ja:"OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください"}[A];k.innerHTML=T.map(v=>{const R=v.match_status,O=v.match_layer;let J="",X="";R==="matched"?(O===1&&(J="matched",X='<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>'),O===2&&(J="matched-l2",X='<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>'),O===3&&(J="matched-l3",X='<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>')):R==="gl_debit_only"||R==="gl_credit_only"?(J="gl-only",X='<span class="brv2-status-badge brv2-badge-gl-only">GL</span>'):(J="stmt-only",X=`<span class="brv2-status-badge brv2-badge-stmt-only">${{zh:"账单",th:"บัญชี",en:"Stmt",ja:"明細"}[A]||"账单"}</span>`);let de="";return v.stmt_balance_ok===!1&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${p(U)}">⚠</span>`,J+=" brv2-row-warn"),v.stmt_confidence==="low"&&(de+=`<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${p(z)}">◌</span>`,J.includes("brv2-row-warn")||(J+=" brv2-row-warn-soft")),`<tr class="${J.trim()}">
              <td>${X}${de}</td>
              <td>${p(c(v.stmt_date))}</td>
              <td title="${p(v.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p(v.stmt_desc)}</td>
              <td class="num">${v.stmt_withdrawal?d(v.stmt_withdrawal):""}</td>
              <td class="num">${v.stmt_deposit?d(v.stmt_deposit):""}</td>
              <td>${p(c(v.gl_date))}</td>
              <td title="${p(v.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${p(v.gl_doc_no)}</td>
              <td class="num">${v.gl_debit?d(v.gl_debit):""}</td>
              <td class="num">${v.gl_credit?d(v.gl_credit):""}</td>
              <td>${O?"L"+O:"—"}</td>
            </tr>`}).join("")}async function Z(){const k=localStorage.getItem("mrpilot_token")||"";try{const A=await(await fetch("/api/recon/bank-v2/tasks",{headers:{Authorization:"Bearer "+k}})).json();ee(A.tasks||[])}catch{const A=l("brv2-history-empty"),U=window._currentLang||"zh",z={zh:"加载失败",th:"โหลดประวัติไม่ได้",en:"Load failed",ja:"読み込み失敗"}[U]||"加载失败";A&&(A.textContent=z,A.style.display="");const v=l("brv2-history-table-wrap");v&&(v.style.display="none")}}const le=10;let ie=1;function V(){const k=l("brv2-history-pager"),T=l("brv2-history-pager-info"),A=l("brv2-history-prev"),U=l("brv2-history-next");if(!k)return;if(u.length<=le){k.style.display="none";return}k.style.display="";const z=Math.ceil(u.length/le);T&&(T.textContent=ie+" / "+z),A&&(A.disabled=ie<=1),U&&(U.disabled=ie>=z)}function Q(){const k=l("brv2-history-prev"),T=l("brv2-history-next");k&&!k._brv2Bound&&(k._brv2Bound=!0,k.addEventListener("click",()=>{ie>1&&(ie--,ee(u))})),T&&!T._brv2Bound&&(T._brv2Bound=!0,T.addEventListener("click",()=>{const A=Math.ceil(u.length/le);ie<A&&(ie++,ee(u))}))}function ee(k){k!==void 0&&(u=k||[],ie=1);const T=u,A=l("brv2-history-empty"),U=l("brv2-history-table-wrap"),z=l("brv2-history-tbody");if(!z)return;const v=window._currentLang||"zh";if(!T.length){const ae={zh:"暂无对账记录",th:"ยังไม่มีประวัติ",en:"No records yet",ja:"記録なし"}[v]||"暂无对账记录";A&&(A.textContent=ae,A.style.display=""),U&&(U.style.display="none"),V();return}A&&(A.style.display="none"),U&&(U.style.display="");const R=Math.ceil(T.length/le);ie>R&&(ie=R);const O=(ie-1)*le,J=T.slice(O,O+le),X=localStorage.getItem("mrpilot_token")||"",de='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>',se='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>',ce='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';z.innerHTML="",J.forEach(ae=>{const pe=Number(ae.formula_diff||0),fe=Math.abs(pe)<.05,me=(ae.stmt_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ge=(ae.gl_files||"").split(";").map(ke=>ke.trim().split(/[/\\]/).pop()).filter(Boolean).join(", "),ye=ae.created_at?String(ae.created_at).slice(0,16).replace("T"," "):"",xe=document.createElement("tr");xe.dataset.taskId=ae.id;const ze=document.createElement("td");ze.textContent=ye;const Te=document.createElement("td");Te.className="glv-history-file",Te.title=me+" + "+ge,Te.textContent=me+" + "+ge;const He=document.createElement("td");He.className="glv-num",He.textContent=(ae.stmt_row_count||0)+" / "+(ae.gl_row_count||0);const it=document.createElement("td");it.className="glv-num",it.textContent=ae.matched_count||0;const rt=document.createElement("td");rt.className="glv-num",rt.textContent=ae.unmatched_gl||0;const lt=document.createElement("td");lt.className="glv-num",lt.textContent=ae.unmatched_stmt||0;const Oe=document.createElement("td");Oe.className="glv-num",Oe.style.color=fe?"#059669":"#dc2626",Oe.textContent=fe?"✓":d(pe);const Ae=document.createElement("td");Ae.className="glv-history-actions";const ct=(ke,St,Ct,_n)=>{const Ie=document.createElement("button");return Ie.type="button",Ie.title=St,Ie.setAttribute("aria-label",St),Ct&&(Ie.className=Ct),Ie.innerHTML=ke,Ie.onclick=kn=>{kn.stopPropagation(),_n()},Ie},gn={zh:"删除这条记录?",th:"ลบรายการนี้?",en:"Delete this record?",ja:"この記録を削除しますか?"}[v]||"删除?",yn={zh:"加载",th:"โหลด",en:"Load",ja:"読込"}[v]||"加载",bn={zh:"导出",th:"ส่งออก",en:"Export",ja:"エクスポート"}[v]||"导出",wn={zh:"删除",th:"ลบ",en:"Delete",ja:"削除"}[v]||"删除";Ae.appendChild(ct(de,yn,"",()=>oe(ae.id,X))),Ae.appendChild(ct(se,bn,"",()=>g(ae.id))),Ae.appendChild(ct(ce,wn,"glv-del",async()=>{await showConfirm(gn,{danger:!0})&&(await fetch("/api/recon/bank-v2/"+ae.id,{method:"DELETE",headers:{Authorization:"Bearer "+X}}),Z())})),[ze,Te,He,it,rt,lt,Oe,Ae].forEach(ke=>xe.appendChild(ke)),xe.style.cursor="pointer",xe.addEventListener("click",async ke=>{ke.target.closest(".glv-del")||ke.target.closest("button")||await oe(ae.id,X)}),z.appendChild(xe)}),V(),ne()}function ne(){const k=((l("brv2-hist-search")||{}).value||"").trim().toLowerCase(),T=l("brv2-history-tbody");T&&T.querySelectorAll("tr").forEach(A=>{A.dataset.taskId&&(A.style.display=!k||A.textContent.toLowerCase().includes(k)?"":"none")})}async function oe(k,T){try{const U=await(await fetch("/api/recon/bank-v2/"+k,{headers:{Authorization:"Bearer "+T}})).json();if(!U.ok)return;o={task_id:U.task_id,...U},i=U.detail||[],s="all",document.querySelectorAll(".brv2-filter-btn").forEach(z=>z.classList.toggle("active",z.dataset.filter==="all")),N(o)}catch{}}function ue(){if(e){Z();return}e=!0,Y("brv2-stmt-zone","brv2-stmt-input","stmt"),Y("brv2-gl-zone","brv2-gl-input","gl");const k=["brv2-anchor-gl-closing","brv2-anchor-stmt-closing","brv2-anchor-stmt-opening","brv2-anchor-gl-opening"];function T(){const O=parseFloat((l("brv2-anchor-stmt-opening")||{}).value),J=parseFloat((l("brv2-anchor-gl-opening")||{}).value),X=l("brv2-anchor-eq"),de=l("brv2-anchor-eq-val");if(!(!X||!de))if(Number.isFinite(O)&&Number.isFinite(J)){const se=O-J;de.textContent=se.toLocaleString(void 0,{minimumFractionDigits:2,maximumFractionDigits:2}),X.style.display=""}else X.style.display="none"}k.forEach(O=>{const J=l(O);J&&(J.addEventListener("input",T),J.addEventListener("input",()=>{const X=J.closest(".brv2-anchor-cell");X&&X.classList.remove("is-prefilled"),_()}))}),j();const A=l("brv2-run-btn");A&&A.addEventListener("click",te);const U=l("brv2-reset-btn");U&&U.addEventListener("click",()=>{o=null,i=[],n=[],a=[],m("stmt"),m("gl"),P(),H(!1);const O=l("brv2-acct-select");O&&(O.style.display="none"),k.forEach(de=>{const se=l(de);if(se){se.value="";const ce=se.closest&&se.closest(".brv2-anchor-cell");ce&&ce.classList.remove("is-prefilled")}});const J=l("brv2-anchor-eq");J&&(J.style.display="none");const X=l("brv2-anchor-prefill-banner");X&&X.classList.remove("show")});const z=l("brv2-new-btn");z&&z.addEventListener("click",()=>{o=null,i=[],n=[],a=[],m("stmt"),m("gl"),P(),H(!1)});const v=l("brv2-filter-tabs");v&&v.addEventListener("click",O=>{O.stopPropagation();const J=O.target.closest(".brv2-filter-btn");J&&(s=J.dataset.filter,v.querySelectorAll(".brv2-filter-btn").forEach(X=>X.classList.toggle("active",X===J)),K())}),B(),Q();const R=l("brv2-hist-search");R&&R.addEventListener("input",ne),Z(),P(),window._brv2LoadHistory=Z,Array.isArray(window.__i18nSubs)||(window.__i18nSubs=[]),window.__i18nSubs=window.__i18nSubs.filter(O=>O.name!=="brv2"),window.__i18nSubs.push({name:"brv2",fn:function(){P(),m("stmt"),m("gl"),o&&N(o),ee()}})}window._loadBankReconV2Panel=function(k){const T=k?document.getElementById(k):null;T&&T.id!=="recon-pane-bank"&&(T.innerHTML=`<div style="padding:16px;font-size:13px;color:var(--ink-3)">
                银行对账 v2 · 请前往对账中心使用</div>`),ue()},document.addEventListener("DOMContentLoaded",()=>{l("brv2-run-btn")&&ue()}),window._bankReconV2Init=ue})();(function(){const e=document.getElementById("general-lang");if(!e)return;e.addEventListener("change",a=>{const o=a.target.value;o&&applyLang(o)});const n=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";e.value=n})();(function(){const n="pearnly_general_tz",a="pearnly_general_date_format",o="pearnly_general_number_format",s={tz:"Asia/Bangkok",date:"YYYY-MM-DD",number:"comma_dot"};function i(){const d=document.getElementById("general-tz"),c=document.getElementById("general-date"),p=document.getElementById("general-number");if(!(!d||!c||!p))try{d.value=localStorage.getItem(n)||s.tz,c.value=localStorage.getItem(a)||s.date,p.value=localStorage.getItem(o)||s.number}catch{d.value=s.tz,c.value=s.date,p.value=s.number}}async function r(){const d=document.getElementById("btn-save-general"),c=document.getElementById("general-save-msg");if(!d)return;const p=d.innerHTML;d.disabled=!0,d.innerHTML="<span>"+(t("msg-saving")||"保存中...")+"</span>",c&&(c.textContent="",c.classList.remove("error"));try{const f=(document.getElementById("general-tz")||{}).value||s.tz,m=(document.getElementById("general-date")||{}).value||s.date,b=(document.getElementById("general-number")||{}).value||s.number;try{localStorage.setItem(n,f),localStorage.setItem(a,m),localStorage.setItem(o,b)}catch{}window._pearnlyGeneral={tz:f,date_format:m,number_format:b},c&&(c.textContent=t("msg-saved")||"已保存")}catch{c&&(c.textContent=t("msg-save-failed")||"保存失败",c.classList.add("error"))}finally{d.disabled=!1,d.innerHTML=p,setTimeout(function(){c&&(c.textContent="")},3e3)}}function u(){const d=document.getElementById("btn-save-general");if(!d){setTimeout(u,200);return}d._pearnlyGenBound||(d._pearnlyGenBound=!0,d.addEventListener("click",r),i())}function l(){i();const d=document.getElementById("general-lang");if(d){const c=typeof currentLang=="string"&&currentLang||localStorage.getItem("mrpilot_lang")||"th";d.value=c}}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",u):u(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("settings-general",l)})();(function(){const e="mrpilot_nav_collapsed",n={ocr:"sales",history:"sales",reconcile:"sales","sales-invoices":"sales",receivables:"sales",vouchers:"expense"};function a(){try{const r=localStorage.getItem(e);return r?JSON.parse(r):{}}catch{return{}}}function o(r){try{localStorage.setItem(e,JSON.stringify(r))}catch{}}function s(){const r=a();document.querySelectorAll(".nav-collapsible").forEach(function(u){const l=u.dataset.collapsible;r[l]?u.classList.add("collapsed"):u.classList.remove("collapsed")})}function i(r){const u=a();u[r]=!u[r],o(u),s()}(function(){const u=a();let l=!1;u.sales===void 0&&(u.sales=!1,l=!0),u.expense===void 0&&(u.expense=!0,l=!0),l&&o(u)})(),s(),document.querySelectorAll(".nav-group-toggle").forEach(function(r){r.addEventListener("click",function(){i(r.dataset.toggleGroup)})}),window.expandNavGroupForRoute=function(r){const u=n[r];if(!u)return;const l=a();l[u]&&(l[u]=!1,o(l),s())}})();const qa=`
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
    </div>`;function At(){const e=document.getElementById("help-modal");if(!e||e.children.length)return;e.innerHTML=qa;const n=window._currentLang||"th",a=window.I18N&&window.I18N[n]||{};e.querySelectorAll("[data-i18n]").forEach(o=>{const s=o.getAttribute("data-i18n");a[s]&&(o.textContent=a[s])})}document.readyState,At();(function(){function e(){const n=document.getElementById("help-modal"),a=document.getElementById("help-modal-close");n&&(a&&!a.dataset.bound&&(a.addEventListener("click",function(){n.style.display="none"}),a.dataset.bound="1"),n.dataset.maskBound||(n.addEventListener("click",function(o){o.target===n&&(n.style.display="none")}),n.dataset.maskBound="1"),window._helpModalEscBound||(document.addEventListener("keydown",function(o){o.key==="Escape"&&n.style.display==="flex"&&(n.style.display="none")}),window._helpModalEscBound=!0))}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",e):e()})();(function(){const e={line:"line",folder:"folder",gmail:"email",erp:"erp",alert:"alert"};document.addEventListener("click",function(n){const a=n.target.closest(".int-btn-configure");if(!a)return;const o=a.closest(".integration-row"),s=o?o.dataset.intAnchor:null;if(s&&e[s]){const i=o.querySelector(".int-name"),r=i?(i.textContent||i.innerText||"").trim():"配置";typeof window.openIntegrationDrawer=="function"&&window.openIntegrationDrawer(e[s],r)}})})();let we=[];window._erpEndpoints=we;let Ne=null;async function ot(){try{const e=await fetch("/api/erp/endpoints",{headers:{Authorization:"Bearer "+token}});if(e.status===401){localStorage.removeItem("mrpilot_token");const a=await e.json().catch(()=>({}));if((typeof a.detail=="string"?a.detail:a.detail&&a.detail.code||"")==="auth.session_revoked"){_showSessionRevokedModal();return}window.location.href="/";return}we=(await e.json()).items||[],window._erpEndpoints=we,ln()}catch(e){console.error("load endpoints failed",e)}}window._refreshErpEndpointsCache=function(){return ot()};async function rn(){const e=document.getElementById("erp-today-stats");if(e){e.innerHTML="";try{const n=await fetch("/api/erp/stats/today",{headers:{Authorization:"Bearer "+token}});if(!n.ok)return;const a=await n.json(),o=a.total||0,s=a.success||0,i=a.failed||0,r=a.auto_cnt||0;if(o===0){e.innerHTML=`<span class="erp-today-empty">${escapeHtml(t("erp-today-none"))}</span>`;return}const u=[];u.push(`<span class="erp-today-item"><strong>${o}</strong> ${escapeHtml(t("erp-today-total"))}</span>`),s>0&&u.push(`<span class="erp-today-item ok"><strong>${s}</strong> ${escapeHtml(t("erp-today-success"))}</span>`),i>0&&u.push(`<span class="erp-today-item fail"><strong>${i}</strong> ${escapeHtml(t("erp-today-failed"))}</span>`),r>0&&u.push(`<span class="erp-today-item auto"><strong>${r}</strong> ${escapeHtml(t("erp-today-auto"))}</span>`),e.innerHTML=u.join("")}catch(n){console.warn("loadErpTodayStats failed",n)}}}function ln(){const e=document.getElementById("erp-endpoints-list"),n=document.getElementById("erp-status-summary"),a=document.getElementById("btn-add-endpoint");if(!e){console.warn("erp-endpoints-list 容器不存在");return}if(a&&_userInfo){const s=_userInfo.endpoints_limit;s!==-1&&we.length>=s?(a.disabled=!0,a.title=t("ep-limit-reached",{limit:s}),a.classList.add("btn-disabled-plus")):(a.disabled=!1,a.title="",a.classList.remove("btn-disabled-plus"))}if(we.length===0){e.innerHTML=`<div class="erp-empty">${escapeHtml(t("ep-list-empty"))}</div>`,n&&(n.textContent=t("auto-status-none"),n.className="auto-status-pill none");return}const o=we.some(s=>s.auto_push&&s.enabled);if(n&&(n.textContent=t("auto-status-active",{n:we.length,mode:o?t("auto-status-on"):t("auto-status-off")}),n.className="auto-status-pill "+(o?"active":"ready")),rn(),e.innerHTML=we.map(s=>{const i=s.config||{},r=escapeHtml(i.url||"");i._token_set;const u=s.enabled!==!1,l=[];s.is_default&&l.push(`<span class="ep-badge default">${escapeHtml(t("ep-default"))}</span>`),s.auto_push&&l.push(`<span class="ep-badge auto">${escapeHtml(t("ep-auto-push-on"))}</span>`),u||l.push(`<span class="ep-badge disabled">${escapeHtml(t("ep-disabled"))}</span>`);const d=[];return s.success_count>0&&d.push(`<span class="ep-stat ok">${escapeHtml(t("ep-success",{n:s.success_count}))}</span>`),s.failure_count>0&&d.push(`<span class="ep-stat fail">${escapeHtml(t("ep-failure",{n:s.failure_count}))}</span>`),`
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
        `}).join(""),_userInfo&&_userInfo.endpoints_limit!==-1){const s=we.length,i=_userInfo.endpoints_limit,r=_userInfo.plan,u=document.createElement("div");u.className="erp-limit-hint",r==="free"?u.innerHTML=`${escapeHtml(t("ep-free-limit-hint",{used:s,limit:i}))} <a data-upgrade="plus">${escapeHtml(t("upgrade-to-plus"))}</a>`:u.textContent=t("ep-plus-limit-hint",{used:s,limit:i}),e.appendChild(u)}}function Ra(e){Ne=e||null;const n=document.getElementById("endpoint-modal"),a=document.getElementById("endpoint-modal-title");a.textContent=e?t("ep-modal-title-edit"):t("ep-modal-title-new");const o=document.getElementById("ep-name"),s=document.getElementById("ep-url"),i=document.getElementById("ep-token"),r=document.getElementById("ep-is-default"),u=document.getElementById("ep-auto-push"),l=document.getElementById("ep-test-result");l.style.display="none",l.textContent="";const d=document.getElementById("ep-save-error");if(d&&d.remove(),e){const p=we.find(f=>f.id===e);if(!p)return;o.value=p.name||"",s.value=(p.config||{}).url||"",i.value=(p.config||{})._token_set&&p.config.token||"",i.placeholder=(p.config||{})._token_set?"（已保存 · 留空保持不变）":t("ep-token-ph"),r.checked=!!p.is_default,u.checked=!!p.auto_push}else o.value="",s.value="",i.value="",i.placeholder=t("ep-token-ph"),r.checked=we.length===0,u.checked=!0;const c=u.closest(".form-switch-row");if(u.disabled=!1,c){c.classList.remove("disabled-plus"),c.title="",c.style.cursor="",c.onclick=null;const p=c.querySelector(".plus-badge");p&&p.remove()}n.style.display="",setTimeout(()=>o.focus(),50)}function cn(){document.getElementById("endpoint-modal").style.display="none",Ne=null;const e=document.getElementById("ep-save-error");e&&e.remove()}function dn(e){if(!e)return"";let n=e.trim();const a=n.search(/\s/);return a>=0&&(n=n.slice(0,a)),n}function pn(){const e=document.getElementById("ep-name").value.trim(),n=dn(document.getElementById("ep-url").value),a=document.getElementById("ep-token").value,o=document.getElementById("ep-is-default").checked,s=document.getElementById("ep-auto-push").checked,i={url:n};return a&&(i.token=a),{name:e,url:n,tokenVal:a,isDefault:o,autoPush:s,config:i}}async function Na(){const{url:e,config:n}=pn(),a=document.getElementById("ep-test-result");if(!e){a.style.display="",a.className="form-test-result fail",a.textContent=t("ep-required");return}a.style.display="",a.className="form-test-result running",a.textContent=t("ep-test-running");try{const s=await(await fetch("/api/erp/test-connection",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({adapter:"webhook",config:n})})).json();s.success?(a.className="form-test-result ok",a.textContent=t("ep-test-ok",{status:s.http_status,ms:s.elapsed_ms})):(a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:s.error_msg||"unknown"}))}catch(o){a.className="form-test-result fail",a.textContent=t("ep-test-fail",{err:o.message})}}async function Fa(){const e=pn(),n=document.getElementById("ep-save-error");if(n&&(n.style.display="none"),!e.name||!e.url){jt(t("ep-required"));return}const a={name:e.name,adapter:"webhook",config:e.config,is_default:e.isDefault,auto_push:e.autoPush},o=document.getElementById("btn-ep-save"),s=o.innerHTML;o.disabled=!0,o.classList.add("loading");try{let i;if(Ne?i=await fetch(`/api/erp/endpoints/${encodeURIComponent(Ne)}`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}):i=await fetch("/api/erp/endpoints",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(a)}),!i.ok){const u=(await i.json().catch(()=>({}))).detail||`HTTP ${i.status}`;throw new Error(typeof u=="string"?u:JSON.stringify(u))}cn(),showToast(t("ep-save-ok")),ot()}catch(i){jt(`${t("ep-save-fail")} · ${i.message||"unknown"}`)}finally{o.disabled=!1,o.classList.remove("loading"),o.innerHTML=s}}function jt(e){let n=document.getElementById("ep-save-error");if(!n){const a=document.querySelector("#endpoint-modal .modal-foot");if(!a)return;n=document.createElement("div"),n.id="ep-save-error",n.className="ep-inline-error",a.parentNode.insertBefore(n,a)}n.textContent=e,n.style.display=""}async function za(e){const n=we.find(o=>o.id===e);if(!(!n||!await showConfirm(t("ep-delete-confirm",{name:n.name}),{danger:!0})))try{if(!(await fetch(`/api/erp/endpoints/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok)throw new Error;showToast(t("ep-delete-ok")),ot()}catch{showToast(t("ep-save-fail"),"fail")}}window.loadErpEndpoints=ot;window.loadErpTodayStats=rn;window.renderErpEndpointsList=ln;window.openEndpointModal=Ra;window.closeEndpointModal=cn;window.saveEndpoint=Fa;window.deleteEndpoint=za;window.testEndpointConnection=Na;window._sanitizeUrl=dn;async function un(e){if(e=(e||"").trim(),!!e)try{await navigator.clipboard.writeText(e),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{try{const a=document.createElement("textarea");a.value=e,a.style.position="fixed",a.style.opacity="0",document.body.appendChild(a),a.select(),document.execCommand("copy"),a.remove(),showToast(t("erp-doc-copy-ok",{no:e}),"success")}catch{showToast(t("erp-doc-copy-fail"),"error")}}}async function Oa(e){const n=document.createElement("div");n.className="log-detail-modal",n.innerHTML=`
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t("log-detail-loading"))}</div>
        </div>
    `,document.body.appendChild(n),n.addEventListener("click",async a=>{if(a.target===n||a.target.classList.contains("log-detail-close")){n.remove();return}const o=a.target.closest("[data-receipt-copy]");if(o){un(o.dataset.receiptCopy);return}const s=a.target.closest("[data-receipt-action]");if(s){const i=s.dataset.receiptAction;i==="retry"?window.retryPushLog(s.dataset.logId):i==="exceptions"?typeof routeTo=="function"&&routeTo("exceptions"):i==="mappings"&&typeof routeTo=="function"&&routeTo("integrations"),n.remove();return}});try{const a=await fetch(`/api/erp/logs/${encodeURIComponent(e)}`,{headers:{Authorization:"Bearer "+token}});if(!a.ok){n.remove();return}const o=await a.json(),s=window._erpEndpoints.find(S=>S.id===o.endpoint_id),i=o.endpoint_name||(s?s.name:o.endpoint_id?t("erp-log-endpoint-deleted"):"-"),r=(o.endpoint_adapter||s&&s.adapter||"").toLowerCase(),u=new Date(o.created_at).toLocaleString(),l=o.trigger==="auto"?t("log-tag-auto"):o.trigger==="retry"?t("log-tag-retry"):t("log-tag-manual"),d=o.request_body?JSON.stringify(o.request_body,null,2):t("erp-receipt-no-tech"),c=o.response_body||t("erp-receipt-no-tech"),p=o.status==="success";let f=typeof c=="string"?c:JSON.stringify(c,null,2);if(p)try{const S=typeof o.response_body=="string"?JSON.parse(o.response_body):o.response_body||{},D=S.row_count||(Array.isArray(S.imported_rows)?S.imported_rows.length:0);D>0&&(f=t("log-push-rows").replace("{n}",String(D)))}catch{}const m=(o.external_doc_no||"").trim(),b=(o.external_url||"").trim(),M=(o.external_doc_hint||"").trim(),I=(o.ocr_buyer_name||"").trim()||o.client_name||"-",x=o.seller_name||"-";let y="-";const $=Number(o.total_amount);o.total_amount!=null&&o.total_amount!==""&&!isNaN($)&&(y=$.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}));const C=p?t("erp-receipt-title-ok"):t("erp-receipt-title-fail"),F=p?"✓":"✗",j=[],_=(S,D)=>{j.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(S)}</span>
                    <span class="erp-receipt-val">${D}</span>
                </div>`)};if(_(t("erp-receipt-invoice-no"),`<strong>${escapeHtml(o.invoice_no||"-")}</strong>`),_(t("erp-receipt-erp-name"),escapeHtml(i)),p){let S;m?S=`<strong class="erp-receipt-docno">${escapeHtml(m)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(m)}" title="${escapeHtml(t("erp-doc-copy-tip"))}">${escapeHtml(t("erp-receipt-copy-btn"))}</button>`:S=`<span class="erp-receipt-docno-missing">${escapeHtml(t("erp-log-doc-missing"))}</span>`,_(t("erp-receipt-doc-no"),S)}_(t("erp-receipt-client"),escapeHtml(I)),_(t("erp-receipt-seller"),escapeHtml(x)),p&&_(t("erp-receipt-amount"),escapeHtml(y)),_(t("erp-receipt-time"),escapeHtml(u)),_(t("erp-receipt-elapsed"),escapeHtml((o.elapsed_ms!=null?o.elapsed_ms:"-")+"ms"));let h="";p&&b?h=`<a class="erp-receipt-primary-btn" href="${escapeHtml(b)}" target="_blank" rel="noopener">${escapeHtml(t("erp-receipt-open-erp"))}</a>`:p&&m&&(h=`<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(m)}">${escapeHtml(t("erp-receipt-copy-docno"))}</button>`);let w="";if(p&&m&&M){const S="erp-receipt-hint-"+M,D=t(S);D&&D!==S&&(w=`<div class="erp-receipt-hint"><svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span>${escapeHtml(D)}</span></div>`)}let L="";if(!p){const S=(o.error_msg||"").match(/ERR_[A-Z0-9_]+/),D=S?S[0]:"",B=typeof currentLang=="string"&&currentLang||window._currentLang||"th",Y=o.error_friendly&&o.error_friendly[B]||(o.error_msg?humanizeError(o.error_msg):t("erp-receipt-no-error")),G=/ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(o.error_msg||""),W=!!(o.history_id&&o.endpoint_id),te=[];te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t("erp-receipt-act-exceptions"))}</button>`),G&&te.push(`<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t("erp-receipt-act-mapping"))}</button>`),W&&te.push(`<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(o.id)}">${escapeHtml(t("erp-receipt-act-retry"))}</button>`),L=`
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t("erp-receipt-fail-reason"))}</div>
                <div class="erp-receipt-fail-box">
                    ${D?`<div class="erp-receipt-errcode">${escapeHtml(D)}</div>`:""}
                    <div class="erp-receipt-friendly">${escapeHtml(Y)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t("erp-receipt-suggest"))}</div>
                <div class="erp-receipt-actions">${te.join("")}</div>`}n.querySelector(".log-detail-box").innerHTML=`
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${p?"ok":"fail"}">${F}</span>
                    ${escapeHtml(C)}
                    <span class="log-tag ${o.trigger}">${escapeHtml(l)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${j.join("")}
            </div>

            ${w}
            ${h?`<div class="erp-receipt-primary-wrap">${h}</div>`:""}
            ${L}

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
                    <pre>${escapeHtml(f)}</pre>
                </div>
            </details>
        `}catch(a){console.error(a),n.remove()}}window.copyErpDocNo=un;window.showLogDetail=Oa;let Be={key:"all",val:""},Ee=new Set;window._erpSelected=Ee;async function Fe(e){const n=document.getElementById("erp-logs-list");if(n){e||(n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-loading"))}</div>`),window.loadErpTodayStats();try{const a=new URLSearchParams({limit:"30"});Be.key==="status"&&a.set("status",Be.val),Be.key==="trigger"&&a.set("trigger",Be.val),Be.key==="adapter"&&a.set("adapter",Be.val);const o=await fetch(`/api/erp/logs?${a}`,{headers:{Authorization:"Bearer "+token}});if(!o.ok){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`;return}const i=(await o.json()).items||[];if(window._erpLogPollTimer&&(clearTimeout(window._erpLogPollTimer),window._erpLogPollTimer=null),i.some(function(d){return d.status==="pending"})&&(window._erpLogPollTimer=setTimeout(function(){Fe(!0)},4e3)),i.length===0){n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-empty"))}</div>`;return}const u='<div class="erp-log-row erp-log-row-header" data-log-header>'+(i.filter(function(d){var c=d.status==="failed"&&d.next_retry_at&&new Date(d.next_retry_at).getTime()>Date.now()-6e4;return!c}).map(function(d){return d.id}).length>0?`<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t("erp-log-select-all-tip"))}">`:'<span class="erp-log-cb-spacer"></span>')+`<span class="log-time">${escapeHtml(t("erp-log-col-time"))}</span><span class="log-status">${escapeHtml(t("erp-log-col-status"))}</span><span class="log-tag-header">${escapeHtml(t("erp-log-col-trigger"))}</span><span class="log-invoice">${escapeHtml(t("erp-log-col-invoice"))}</span><span class="log-workspace">${escapeHtml(t("erp-log-col-workspace"))}</span><span class="log-client">${escapeHtml(t("erp-log-col-client"))}</span><span class="log-seller">${escapeHtml(t("erp-log-col-seller"))}</span><span class="log-erp">${escapeHtml(t("erp-log-col-erp"))}</span><span class="log-doc">${escapeHtml(t("erp-log-col-doc"))}</span><span class="log-http">${escapeHtml(t("erp-log-col-http"))}</span><span class="log-elapsed">${escapeHtml(t("erp-log-col-elapsed"))}</span><span class="log-actions"></span></div>`;n.innerHTML=u+i.map(d=>{const c=new Date(d.created_at),p=`${String(c.getMonth()+1).padStart(2,"0")}-${String(c.getDate()).padStart(2,"0")} ${String(c.getHours()).padStart(2,"0")}:${String(c.getMinutes()).padStart(2,"0")}`,f=d.status==="failed"&&d.next_retry_at&&new Date(d.next_retry_at).getTime()>Date.now()-6e4;let m,b,M;d.status==="pending"?(m="retrying",b="⟳",M=t("erp-status-pending")):d.status==="success"?(m="ok",b="✓",M=t("erp-status-success")):d.status==="skipped_dup"?(m="skipped",b="⏭",M=t("erp-status-skipped")):f?(m="retrying",b="↻",M=t("erp-status-retrying")):(m="fail",b="✗",M=t("erp-status-failed"));let I;d.trigger==="auto"?I=`<span class="log-tag auto">${escapeHtml(t("log-tag-auto"))}</span>`:d.trigger==="retry"?I=`<span class="log-tag retry">${escapeHtml(t("log-tag-retry"))}</span>`:I=`<span class="log-tag manual">${escapeHtml(t("log-tag-manual"))}</span>`;let x="";const y=d.retry_count||0,$=d.max_retries||3;if(f){const Y=new Date(d.next_retry_at).getTime()-Date.now(),G=Math.max(0,Math.round(Y/6e4)),W=G<=0?t("erp-retry-next-soon"):t("erp-retry-next-min",{n:G});x=`${t("erp-retry-attempt",{n:y,max:$})} · ${W}`}else d.status==="failed"&&y>=$&&!d.next_retry_at&&(x=t("erp-retry-exhausted",{n:y}));const C=d.status==="failed"&&!f?`<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(d.id)}" title="${escapeHtml(t("log-retry-title"))}">↻</button>`:"",F=!f,j=Ee.has(d.id)?"checked":"",_=F?`<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(d.id)}" ${j}>`:'<span class="erp-log-cb-spacer"></span>',h=(d.ocr_buyer_name||"").trim()||(d.client_name||"").trim(),w=h?`<span class="log-client" title="${escapeHtml(h)}">${escapeHtml(h.substring(0,18))}</span>`:`<span class="log-client log-client-empty" title="${escapeHtml(t("erp-log-client-unassigned-tip"))}">${escapeHtml(t("erp-log-client-unassigned"))}</span>`,L=d.workspace_name?`<span class="log-workspace">${escapeHtml((d.workspace_name||"").substring(0,16))}</span>`:`<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t("erp-log-ws-unresolved-tip"))}">${escapeHtml(t("erp-log-ws-unresolved"))}</span>`,S=d.endpoint_name?`<span class="log-erp">${escapeHtml((d.endpoint_name||"").substring(0,14))}</span>`:`<span class="log-erp log-erp-deleted">${escapeHtml(t("erp-log-endpoint-deleted"))}</span>`,D=(d.external_doc_no||"").trim(),B=(d.external_url||"").trim();let P;return B?P=`<span class="log-doc"><a href="${escapeHtml(B)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(D||"")}">${escapeHtml(t("erp-log-doc-open"))}</a></span>`:D?P=`<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(D)}" title="${escapeHtml(t("erp-log-doc-copy-tip"))}">${escapeHtml(D.substring(0,18))}</span>`:d.status==="success"?P=`<span class="log-doc log-doc-missing" title="${escapeHtml(t("erp-log-doc-missing-tip"))}">${escapeHtml(t("erp-log-doc-missing"))}</span>`:P='<span class="log-doc log-doc-empty">-</span>',`
                <div class="erp-log-row ${m}" data-log-detail="${escapeHtml(d.id)}">
                    ${_}
                    <span class="log-time">${p}</span>
                    <span class="log-status" title="${escapeHtml(M+(x?" · "+x:""))}">${b}</span>
                    ${I}
                    <span class="log-invoice">${escapeHtml(d.invoice_no||"-")}</span>
                    ${L}
                    ${w}
                    <span class="log-seller">${escapeHtml((d.seller_name||"").substring(0,20))}</span>
                    ${S}
                    ${P}
                    <span class="log-http">HTTP ${d.http_status||"-"}</span>
                    <span class="log-elapsed">${d.elapsed_ms}ms</span>
                    <span class="log-actions">${C}</span>
                </div>
            `}).join("");const l=new Set(i.map(d=>d.id));for(const d of Array.from(Ee))l.has(d)||Ee.delete(d);window._refreshErpBatchBar()}catch(a){console.error("load erp logs failed",a),n.innerHTML=`<div class="erp-logs-empty">${escapeHtml(t("erp-logs-error"))}</div>`}}}async function fn(e){try{const n=await fetch(`/api/erp/logs/${encodeURIComponent(e)}/retry`,{method:"POST",headers:{Authorization:"Bearer "+token}}),a=await n.json().catch(()=>({}));n.ok&&a.ok?showToast(t("log-retry-ok"),"success"):showToast(t("log-retry-fail")+" · HTTP "+(a.http_status||n.status),"error"),Fe(),window.loadErpEndpoints()}catch{showToast(t("log-retry-fail"),"error")}}(function(){document.getElementById("btn-add-endpoint").addEventListener("click",()=>window.openEndpointModal(null)),document.getElementById("endpoint-modal-close").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-cancel").addEventListener("click",window.closeEndpointModal),document.getElementById("btn-ep-test").addEventListener("click",window.testEndpointConnection),document.getElementById("btn-ep-save").addEventListener("click",window.saveEndpoint),document.getElementById("ep-url").addEventListener("blur",n=>{const a=window._sanitizeUrl(n.target.value);a!==n.target.value.trim()&&(n.target.value=a)}),document.addEventListener("click",n=>{const a=n.target.closest("[data-ep-edit]"),o=n.target.closest("[data-ep-del]");a&&window.openEndpointModal(a.dataset.epEdit),o&&window.deleteEndpoint(o.dataset.epDel);const s=n.target.closest("[data-log-retry]");if(s){n.stopPropagation(),fn(s.dataset.logRetry);return}const i=n.target.closest("[data-log-cb]");if(i){n.stopPropagation();const c=i.dataset.logCb;i.checked?Ee.add(c):Ee.delete(c),window._refreshErpBatchBar();return}const r=n.target.closest("[data-log-select-all]");if(r){n.stopPropagation();const c=r.checked;document.querySelectorAll("[data-log-cb]").forEach(function(f){f.checked=c;const m=f.dataset.logCb;c?Ee.add(m):Ee.delete(m)}),window._refreshErpBatchBar();return}if(n.target.closest("#btn-erp-batch-retry")){n.stopPropagation(),window._runErpBatchRetry();return}if(n.target.closest("#btn-erp-batch-clear")){n.stopPropagation(),Ee.clear(),document.querySelectorAll(".erp-log-cb").forEach(c=>{c.checked=!1}),window._refreshErpBatchBar();return}const u=n.target.closest("[data-log-detail]");if(u){if(n.target.closest("[data-log-cb]"))return;const c=n.target.closest("[data-copy-doc]");if(c){n.stopPropagation(),window.copyErpDocNo(c.dataset.copyDoc);return}if(n.target.closest(".log-doc-open"))return;window.showLogDetail(u.dataset.logDetail);return}const l=n.target.closest(".chip-filter");if(l){document.querySelectorAll("#erp-logs-filters .chip-filter").forEach(c=>c.classList.remove("active")),l.classList.add("active"),Be={key:l.dataset.filterKey,val:l.dataset.filterVal},Fe();return}if(n.target.closest("#btn-refresh-logs")){const c=n.target.closest("#btn-refresh-logs");c.classList.add("spinning"),setTimeout(()=>c.classList.remove("spinning"),600),Fe();return}const d=n.target.closest(".auto-nav-item");if(d&&d.dataset.autoTab){switchAutomationTab(d.dataset.autoTab);return}})})();window.loadErpLogs=Fe;window.retryPushLog=fn;function mn(){const e=document.getElementById("erp-logs-batch-bar"),n=document.getElementById("erp-logs-batch-count"),a=document.querySelector("[data-log-select-all]");if(a){const i=document.querySelectorAll("[data-log-cb]").length,r=window._erpSelected.size;r===0?(a.checked=!1,a.indeterminate=!1):r>=i?(a.checked=!0,a.indeterminate=!1):(a.checked=!1,a.indeterminate=!0)}if(!e||!n)return;const o=window._erpSelected.size;if(o===0){e.style.display="none";return}e.style.display="",n.textContent=t("erp-batch-selected",{n:o})}async function vn(){console.info("[ErpBatch] retry triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-confirm",{n:e.length})))try{const a=await fetch("/api/erp/logs/batch-retry",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!a.ok){showToast(t("erp-logs-error"),"error");return}const o=await a.json(),s=t("erp-batch-result",{ok:o.succeeded||0,fail:o.failed||0,skip:o.skipped||0}),i=o.failed&&o.failed>0?"warn":"success";showToast(s,i),window._erpSelected.clear(),window.loadErpLogs()}catch(a){console.error("batch retry failed",a),showToast(t("erp-logs-error"),"error")}}async function hn(){console.info("[ErpBatch] delete triggered · selected=",window._erpSelected.size);const e=Array.from(window._erpSelected);if(e.length===0){showToast(t("erp-batch-empty-warn"),"warn");return}if(await showConfirm(t("erp-batch-delete-confirm",{n:e.length}),{danger:!0}))try{const o=await fetch("/api/erp/logs/batch-delete",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({log_ids:e})});if(!o.ok){showToast(t("erp-logs-error"),"error");return}const s=await o.json();e.forEach(function(i){var r=document.querySelector('[data-log-detail="'+i+'"]');r&&r.remove()});var a=document.getElementById("erp-logs-batch-bar");a&&(a.style.display="none"),showToast(t("erp-batch-delete-result",{n:s.deleted||0,skip:s.skipped||0}),s.deleted>0?"success":"warn"),window._erpSelected.clear(),setTimeout(window.loadErpLogs,500)}catch(o){console.error("batch delete failed",o),showToast(t("erp-logs-error"),"error")}}(function(){function n(){var a=document.getElementById("btn-erp-batch-retry"),o=document.getElementById("btn-erp-batch-delete"),s=document.getElementById("btn-erp-batch-clear");a&&!a.dataset.boundDirect&&(a.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),vn()}),a.dataset.boundDirect="1"),o&&!o.dataset.boundDirect&&(o.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),hn()}),o.dataset.boundDirect="1"),s&&!s.dataset.boundDirect&&(s.addEventListener("click",function(i){i.preventDefault(),i.stopPropagation(),window._erpSelected.clear(),document.querySelectorAll(".erp-log-cb").forEach(function(r){r.checked=!1}),mn()}),s.dataset.boundDirect="1")}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",n):n(),setTimeout(n,2e3),setTimeout(n,5e3),window._bindErpBatchButtons=n})();window._refreshErpBatchBar=mn;window._runErpBatchRetry=vn;window._runErpBatchDelete=hn;(function(){let e=null,n=!1;function a(){if(e)return e;const u=document.createElement("div");u.id="line-email-modal",u.style.cssText="position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;",u.innerHTML=`
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
        `,document.body.appendChild(u),e=u;const l=u.querySelector("#line-email-input"),d=u.querySelector("#line-email-submit-btn"),c=u.querySelector("#line-email-err");async function p(){c.textContent="";const f=(l.value||"").trim().toLowerCase();if(!f||f.indexOf("@")<0||f.split("@")[1].indexOf(".")<0){c.textContent=t("line-email-err-invalid");return}d.disabled=!0,d.style.opacity="0.6";try{const m=await fetch("/api/me/line_complete_email",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+(localStorage.getItem("mrpilot_token")||"")},body:JSON.stringify({email:f})});if(!m.ok)throw new Error("http_"+m.status);const b=await m.json();b.token&&localStorage.setItem("mrpilot_token",b.token),typeof showToast=="function"&&showToast(b.merged?t("line-email-merged-toast"):t("line-email-saved-toast"),"success"),setTimeout(function(){window.location.reload()},600)}catch{c.textContent=t("line-email-err-failed"),d.disabled=!1,d.style.opacity="1"}}return d.addEventListener("click",p),l.addEventListener("keydown",function(f){f.key==="Enter"&&p()}),u}function o(){if(!e)return;const u=e.querySelector("#line-email-title-h"),l=e.querySelector("#line-email-sub-p"),d=e.querySelector("#line-email-input"),c=e.querySelector("#line-email-submit-btn");u&&(u.textContent=t("line-email-title")),l&&(l.textContent=t("line-email-sub")),d&&(d.placeholder=t("line-email-placeholder")),c&&(c.textContent=t("line-email-submit"))}function s(){a(),o(),e.style.display="flex",n=!0;const u=e.querySelector("#line-email-input");u&&setTimeout(function(){u.focus()},100)}async function i(){const u=localStorage.getItem("mrpilot_token");if(u)try{const l=await fetch("/api/me/needs_email",{headers:{Authorization:"Bearer "+u}});if(!l.ok)return;const d=await l.json();d&&d.needs_email&&s()}catch{}}function r(){setTimeout(i,800)}document.readyState==="loading"?document.addEventListener("DOMContentLoaded",r):r(),typeof window.subscribeI18n=="function"&&window.subscribeI18n("line-email-modal",function(){n&&o()})})();(function(){function e(c){let p=0;return c.length>=8&&p++,c.length>=12&&p++,/[a-zA-Z]/.test(c)&&/\d/.test(c)&&p++,/[^a-zA-Z0-9]/.test(c)&&p++,Math.min(3,p)}function n(c,p){const f=document.getElementById("cpw-msg");f&&(f.textContent=c,f.className="cpw-msg "+(p||""))}function a(c){return typeof t=="function"?t(c):c}let o=!1;function s(){["cpw-old","cpw-new","cpw-confirm"].forEach(p=>{const f=document.getElementById(p);f&&(f.value="",f.setAttribute("readonly","readonly"))});const c=document.getElementById("cpw-strength-bar");c&&(c.style.width="0%",c.className="cpw-strength-bar"),n("","")}async function i(){const c=document.getElementById("btn-change-pw"),p=document.getElementById("cpw-old"),f=document.getElementById("cpw-new"),m=document.getElementById("cpw-confirm"),b=document.getElementById("cpw-strength-bar");if(!c||!p||!f||!m)return;const M=p.value,I=f.value,x=m.value;if(!M||!I||!x){n(a("settings-change-pw-empty"),"error");return}if(I.length<8){n(a("settings-change-pw-too-short"),"error");return}if(!(/[a-zA-Z]/.test(I)&&/\d/.test(I))){n(a("settings-change-pw-too-weak"),"error");return}if(I!==x){n(a("settings-change-pw-mismatch"),"error");return}c.disabled=!0;const y=c.textContent;c.textContent=a("settings-change-pw-submitting"),n("","");try{const $=localStorage.getItem("mrpilot_token"),C=await fetch("/api/me/change_password",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+$},body:JSON.stringify({old_password:M,new_password:I})}),F=await C.json().catch(()=>({}));if(C.ok&&F.ok)n(a("settings-change-pw-success"),"success"),typeof showToast=="function"&&showToast(a("settings-change-pw-success"),"success"),p.value="",f.value="",m.value="",b&&(b.style.width="0%",b.className="cpw-strength-bar");else{const j=F.detail||"";let _=a("settings-change-pw-success");j==="wrong_old_password"?_=a("settings-change-pw-wrong-old"):j==="password_too_short"?_=a("settings-change-pw-too-short"):j==="password_too_weak"?_=a("settings-change-pw-too-weak"):_=j||"Error",n(_,"error")}}catch($){console.error("change_password",$),n("Network error","error")}finally{c.disabled=!1,c.textContent=y}}function r(){o||(o=!0,document.addEventListener("click",c=>{if(!c.target||!c.target.closest)return;const p=c.target.closest(".cpw-eye");if(p){const f=document.getElementById(p.dataset.target);f&&(f.type=f.type==="password"?"text":"password");return}if(c.target.closest("#cpw-forgot-link")){c.preventDefault(),u();return}if(c.target.closest("#btn-change-pw")){i();return}c.target.closest('.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]')&&setTimeout(s,100)}),document.addEventListener("input",c=>{if(c.target&&c.target.id==="cpw-new"){const p=document.getElementById("cpw-strength-bar");if(!p)return;const f=e(c.target.value),m=["0%","33%","66%","100%"],b=["","weak","medium","strong"];p.style.width=m[f],p.className="cpw-strength-bar "+b[f]}}),document.addEventListener("focusin",c=>{c.target&&["cpw-old","cpw-new","cpw-confirm"].includes(c.target.id)&&c.target.removeAttribute("readonly")}),document.getElementById("cpw-old")&&s())}function u(){const c=window._userInfo||(typeof _userInfo<"u"?_userInfo:null),p=c&&c.username?c.username:"",f=l(p);let m=document.getElementById("cpw-forgot-overlay");m&&m.remove(),m=document.createElement("div"),m.id="cpw-forgot-overlay",m.className="cpw-forgot-overlay",m.innerHTML=`
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${d(a("cpw-forgot-title"))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${d(a("cpw-forgot-desc"))}</p>
                    <div class="cpw-forgot-email">${d(f)}</div>
                    <p class="cpw-forgot-tip">${d(a("cpw-forgot-tip"))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${d(a("cpw-forgot-cancel"))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${d(a("cpw-forgot-send"))}</button>
                </div>
            </div>
        `,document.body.appendChild(m);const b=()=>m.remove();m.querySelector("#cpw-forgot-close").addEventListener("click",b),m.querySelector("#cpw-forgot-cancel").addEventListener("click",b),m.addEventListener("click",M=>{M.target===m&&b()}),m.querySelector("#cpw-forgot-send").addEventListener("click",async()=>{const M=m.querySelector("#cpw-forgot-send"),I=m.querySelector("#cpw-forgot-msg");M.disabled=!0;const x=M.textContent;M.textContent=a("cpw-forgot-sending");try{const y=await fetch("/api/auth/forgot_password",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:p})}),$=await y.json().catch(()=>({}));y.ok?(I.textContent=a("cpw-forgot-success"),I.className="cpw-forgot-msg success",M.style.display="none",m.querySelector("#cpw-forgot-cancel").textContent=a("cpw-forgot-close-btn")):(I.textContent=$.detail||a("cpw-forgot-fail"),I.className="cpw-forgot-msg error",M.disabled=!1,M.textContent=x)}catch{I.textContent=a("cpw-forgot-fail"),I.className="cpw-forgot-msg error",M.disabled=!1,M.textContent=x}})}function l(c){if(!c||!c.includes("@"))return c||"";const[p,f]=c.split("@");return p.length<=2?p+"****@"+f:p.slice(0,2)+"****@"+f}function d(c){return c==null?"":String(c).replace(/[&<>"']/g,p=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[p])}document.readyState==="complete"||document.readyState==="interactive"?r():document.addEventListener("DOMContentLoaded",r)})();(function(){let e=null,n=!1;async function a(){if(n)return;const s=localStorage.getItem("mrpilot_token");if(s){n=!0;try{const i=await fetch("/api/me",{headers:{Authorization:"Bearer "+s},cache:"no-store"});if(i.status===401){const r=await i.json().catch(()=>({})),u=r&&r.detail;let l="";if(typeof u=="string"?l=u:u&&typeof u=="object"&&(l=u.code||""),console.warn("[heartbeat] session revoked",l),localStorage.removeItem("mrpilot_token"),e&&(clearInterval(e),e=null),l==="auth.session_revoked")try{_showSessionRevokedModal()}catch{window.location.href="/"}else{const d=l==="auth.password_changed_relogin"?"alert-password-changed-relogin":"alert-session";try{typeof showToast=="function"&&typeof t=="function"?showToast(t(d),"error"):alert("Session expired")}catch{}setTimeout(()=>{window.location.href="/"},1500)}}}catch{}finally{n=!1}}}function o(){e&&clearInterval(e),e=setInterval(a,15e3)}localStorage.getItem("mrpilot_token")&&o(),window.addEventListener("focus",a),document.addEventListener("visibilitychange",function(){document.hidden||a()}),window._sessionCheck=a})();async function st(){const e=document.getElementById("team-loading"),n=document.getElementById("team-list"),a=document.getElementById("team-empty"),o=document.getElementById("team-count");if(n){e&&(e.style.display=""),n.style.display="none",a&&(a.style.display="none");try{const s=await apiGet("/api/team/employees"),i=s&&s.employees||[];if(e&&(e.style.display="none"),o&&(o.textContent=(t("team-count")||"共 {n} 名员工").replace("{n}",i.length)),i.length===0){a&&(a.style.display="");return}n.style.display="",n.innerHTML=i.map(r=>{const u=r.last_login_at?new Date(r.last_login_at).toLocaleDateString():t("team-never-login")||"从未登录",l=r.is_active===!1?"team-status-off":"team-status-on",d=r.is_active===!1?t("team-status-disabled")||"已禁用":t("team-status-active")||"正常",c=r.email?`<span class="team-meta-sep">·</span><span>${escapeHtml(r.email)}</span>`:"";return`
            <div class="team-card" data-employee-id="${escapeHtml(r.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((r.username||"?")[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(r.username||"")}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${l}"></span>
                            <span>${escapeHtml(d)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t("team-last-login")||"上次登录")}: ${escapeHtml(u)}</span>
                            ${c}
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
            </div>`}).join("")}catch(s){console.error("loadTeamList failed:",s),e&&(e.textContent=t("team-load-failed")||"加载失败")}}}async function Va(){document.querySelectorAll(".add-emp-overlay").forEach(o=>o.remove());const e=document.createElement("div");e.className="add-emp-overlay",e.innerHTML=`
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
    `,document.body.appendChild(e),requestAnimationFrame(()=>e.classList.add("show")),setTimeout(()=>{const o=document.getElementById("add-emp-username");o&&o.focus()},200);function n(){e.classList.remove("show"),setTimeout(()=>e.remove(),220)}e.querySelector(".add-emp-close").addEventListener("click",n),e.querySelector("#add-emp-cancel").addEventListener("click",n),e.addEventListener("click",o=>{o.target===e&&n()}),e.querySelector("#add-emp-submit").addEventListener("click",async()=>{const o=document.getElementById("add-emp-username"),s=document.getElementById("add-emp-email"),i=document.getElementById("add-emp-password"),r=document.getElementById("add-emp-msg"),u=document.getElementById("add-emp-submit"),l=(o.value||"").trim(),d=(s.value||"").trim(),c=i.value||"";if(r.textContent="",r.classList.remove("error"),!l||l.length<3){r.textContent=t("team-modal-err-username")||"用户名至少 3 位",r.classList.add("error");return}if(!/^[a-zA-Z0-9_.\-]+$/.test(l)){r.textContent=t("team-modal-err-username-fmt")||"只能用字母 / 数字 / 下划线 / 点 / 横线",r.classList.add("error");return}if(d&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d)){r.textContent=t("msg-email-invalid")||"邮箱格式不对",r.classList.add("error");return}if(c.length<8){r.textContent=t("pwd-too-short")||"密码至少 8 位",r.classList.add("error");return}if(/^\d+$/.test(c)){r.textContent=t("pwd-too-weak-numeric")||"不能是纯数字 · 请加入字母",r.classList.add("error");return}if(!(/[a-zA-Z]/.test(c)&&/\d/.test(c))){r.textContent=t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字",r.classList.add("error");return}u.disabled=!0,u.textContent=t("msg-saving")||"保存中...";try{const p={username:l,password:c};d&&(p.email=d);const f=await apiPost("/api/team/employees",p),m=f?await f.json().catch(()=>({})):{};if(f&&f.ok&&m&&m.ok){showToast(t("team-added")||"员工已添加","success"),n(),st();return}const b=m&&m.detail||"unknown",M={"team.username_exists":t("team-username-exists")||"用户名已被占用","team.email_exists":t("team-email-exists")||"邮箱已被占用","team.create_failed":t("team-create-failed")||"创建失败","team.only_owner_or_super":t("team-no-permission")||"无权限","team.no_tenant":t("team-no-tenant")||"请先升级账号","pwd.too_short":t("pwd-too-short")||"密码至少 8 位","pwd.too_weak_numeric":t("pwd-too-weak-numeric")||"不能是纯数字","pwd.too_weak_common":t("pwd-too-weak-common")||"这个密码太常见 · 请换一个","pwd.too_weak":t("pwd-too-weak")||"密码至少 8 位 · 字母 + 数字"};r.textContent=M[b]||(t("team-create-failed")||"创建失败")+" ("+b+")",r.classList.add("error")}catch{r.textContent=t("team-create-failed")||"创建失败",r.classList.add("error")}finally{u.disabled=!1,u.textContent=t("team-add")||"添加员工"}});function a(o){o.key==="Escape"&&(n(),document.removeEventListener("keydown",a))}document.addEventListener("keydown",a)}async function Ua(e,n){try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}/active`,{method:"PATCH",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({is_active:!!n})})).ok){st();return}showToast(t("team-toggle-failed")||"操作失败","error")}catch{showToast(t("team-toggle-failed")||"操作失败","error")}}async function Ga(e,n){const o=(t("team-confirm-remove")||"确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{danger:!0,okText:t("team-remove")}))try{if((await fetch(`/api/team/employees/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Authorization:"Bearer "+token}})).ok){showToast(t("team-removed")||"已移除","success"),st();return}showToast(t("team-remove-failed")||"移除失败","error")}catch{showToast(t("team-remove-failed")||"移除失败","error")}}async function Ka(e,n){const o=(t("team-reset-pwd-confirm")||"给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码").replace("{name}",n).replace("{n}",n);if(await showConfirm(o,{okText:t("team-reset-link-send-btn")||"发送链接"}))try{const i=await fetch(`/api/team/employees/${encodeURIComponent(e)}/reset-password`,{method:"POST",headers:{Authorization:"Bearer "+token}}),r=await i.json().catch(()=>({}));if(i.status===400&&r.detail==="team.reset_no_channel"){showToast(t("team-reset-no-channel")||"员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置","error");return}if(!i.ok){showToast(t("team-reset-pwd-fail")||"发送失败","error");return}if(r.channel==="line"||r.channel==="email"){const u=t("team-reset-link-sent")||"改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效",l=r.channel==="line"?"LINE":t("team-reset-via-email")||"邮箱";showToast(u.replace("{ch}",l),"success");return}showToast(t("team-reset-pwd-fail")||"发送失败","error")}catch{showToast(t("team-reset-pwd-fail")||"发送失败","error")}}document.addEventListener("click",e=>{if(e.target.closest("#btn-add-employee")){e.preventDefault(),Va();return}const n=e.target.closest("[data-toggle-employee]");if(n){e.preventDefault(),Ua(n.dataset.toggleEmployee,n.dataset.active==="false");return}const a=e.target.closest("[data-remove-employee]");if(a){e.preventDefault(),Ga(a.dataset.removeEmployee,a.dataset.name||"");return}const o=e.target.closest("[data-reset-pwd-employee]");if(o){e.preventDefault(),Ka(o.dataset.resetPwdEmployee,o.dataset.name||"");return}const s=e.target.closest("[data-assign-clients]");if(s){e.preventDefault(),typeof window.openAssignClientsModal=="function"&&window.openAssignClientsModal(s.dataset.assignClients,s.dataset.name||"");return}});window.loadTeamList=st;function Ja(e){document.querySelectorAll(".auto-nav-item").forEach(n=>{n.classList.toggle("active",n.dataset.autoTab===e)}),document.querySelectorAll(".auto-panel").forEach(n=>{n.classList.toggle("active",n.dataset.autoPanel===e)}),e==="email"&&typeof window._loadEmailIngestPanel=="function"?(window._loadEmailIngestPanel(),typeof window._startEmailLogAutoRefresh=="function"&&window._startEmailLogAutoRefresh()):typeof window._stopEmailLogAutoRefresh=="function"&&window._stopEmailLogAutoRefresh(),e==="bank"&&typeof window._loadBankReconPanel=="function"&&window._loadBankReconPanel(),e==="linebot"&&typeof window._loadLineBotPanel=="function"&&window._loadLineBotPanel(),e==="alert"&&typeof window._loadNotificationsPanel=="function"&&window._loadNotificationsPanel(),e==="folder"&&typeof window._loadFolderWatcherPanel=="function"&&window._loadFolderWatcherPanel()}window.switchAutomationTab=Ja;typeof console<"u"&&typeof console.info=="function"&&console.info("[pearnly] vite bundle loaded · dashboard + billing + test-center + workspace-switcher + recon-center + assign-clients + access-log + notifications + recon-batch + welcome-wizard + archive-settings");
//# sourceMappingURL=main.js.map
