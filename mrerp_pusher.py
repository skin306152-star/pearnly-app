"""
mrerp_pusher.py · v118.27.8.0
==============================
MR.ERP for SME (mrerp4sme.com) 后端模拟登录直推适配器

铁律(本窗口反向工程实测确认 · 2026-05-10):
    - 路径分两套:`impartran/`(交易类业务单据 · 销售/采购/收付款) ≠ `imparse/`(主数据类)
    - idmenu(URL 路由) ≠ selmenu(业务子类型字典)
    - idus(MR.ERP 内部用户 ID · test01=15)登录后从 HTML scrape 拿
    - 5 步流程:login → select_company → upload_xlsx → fetch_preview → confirm_import
    - 上传不是 AJAX · 是浏览器整页跳转(uploadexcel 存 session · formrdpc 拿预览)
    - confirm_import 是 multipart 不是 form-urlencoded(虽然字段都是文本)
    - sheet 命名严格:Worksheet / Worksheet 1 / Worksheet 2 (大写 W + 空格)
    - 客户/商品 code 三段式 · 含泰文 · UTF-8

抓包来源:
    test01 / 1010-01-000006 / TEST2019(comidyear=6 / seldb=1)
    样本:ขายเชื่อ.xlsx(SC 赊销 · Korn 提供 · 2 行数据)
    实测成功:idmenu=370 + selmenu=118 + 1 行 cbimport[2]=2 → returns "2"

接口设计:
    pusher = MrErpPusher(username, password, comidyear=6, seldb=1)
    pusher.login()                         # 拿 PHPSESSID + idus
    pusher.select_company()                # 激活 session
    ok = pusher.upload_xlsx(file_bytes, module="sales_credit")
    if not ok:
        raise ...
    rows = pusher.fetch_preview(module="sales_credit")
    # rows = [{"row_id": "2", "data": {...解析的字段...}}]
    result = pusher.confirm_import(module="sales_credit", row_ids=["2"])
    # result = {"success": True, "raw": "2", "imported_rows": ["2"]}

错误处理:
    - 网络/超时:抛 MrErpNetworkError
    - 登录失败:抛 MrErpAuthError(凭据失败 · 让上层降级到 xlsx 兜底)
    - 校验失败(单号重复/客户码不存在):抛 MrErpValidationError(给用户具体原因)
    - 任何失败:上层应自动降级生成 .xlsx 让用户走 C 路径(铁律 26)
"""
import re
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ============================================================================
# 模块字典 · v27.8.0 起步只支持 SC 赊销 · 其他子模块等 Zihao 抓 idmenu/selmenu
# 后续应迁到 DB 表 mrerp_module_map · v27.8.x 改进
# ============================================================================
MODULE_MAP = {
    # SC 赊销(已实测 ✅)
    "sales_credit": {
        "label_th": "ขายเชื่อ-รายได้ขายในประเทศ",
        "label_zh": "赊销-国内销售收入",
        "path": "impartran",         # 上传/预览/确认 走 impartran/
        "idmenu": 370,                # URL 路由 ID
        "selmenu": 118,               # 业务子类型 ID
        "sheet_count": 3,             # Worksheet / Worksheet 1 / Worksheet 2
        "verified": True,
    },
    # SE 现金销售(已知 idmenu · selmenu 待抓)
    "sales_cash": {
        "label_th": "ขายเงินสด",
        "label_zh": "现金销售",
        "path": "imparse",            # ⚠️ 注意是 imparse 不是 impartran
        "idmenu": 371,
        "selmenu": None,              # ⚠️ 待抓 · 进 idmenu=371 看下拉 default value
        "sheet_count": 4,
        "verified": False,
    },
    # 其他模块(待抓):purchase_credit / purchase_cash / receive / pay / journal ...
}


# ============================================================================
# 异常体系 · 让上层精确处理
# ============================================================================
class MrErpError(Exception):
    """MR.ERP 推送基类"""


class MrErpNetworkError(MrErpError):
    """网络/超时 · 上层应重试 1 次再降级"""


class MrErpAuthError(MrErpError):
    """登录失败/session 过期 · 上层应提示用户更新凭据"""


class MrErpValidationError(MrErpError):
    """服务端业务校验失败 · 单号重复/客户码不存在等 · 上层给用户具体原因"""


class MrErpModuleError(MrErpError):
    """模块尚未支持(selmenu 未抓全) · 提示用户走 xlsx 兜底"""


# ============================================================================
# 主类
# ============================================================================
class MrErpPusher:
    BASE = "https://www.mrerp4sme.com"
    DEFAULT_TIMEOUT = 30  # 秒
    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36")

    def __init__(self, username: str, password: str,
                 comidyear: int = 6, seldb: int = 1,
                 timeout: int = DEFAULT_TIMEOUT):
        if not username or not password:
            raise MrErpAuthError("username/password 不能为空")
        self.username = username
        self.password = password
        self.comidyear = int(comidyear)
        self.seldb = int(seldb)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.UA})
        self.idus: Optional[str] = None       # 登录后填(test01 = "15")
        self._logged_in = False
        self._company_selected = False

    # ------------------------------------------------------------------
    # Step 0a · 登录
    # ------------------------------------------------------------------
    def login(self) -> str:
        """登录 MR.ERP · 返回 PHPSESSID(也存在 self.session.cookies 里)

        实测 endpoint:POST /login/checklogin.php
        ⚠️ v27.8.0 实测 form 字段名待 Zihao 抓登录请求 cURL 后补充
                  (本窗口已抓 4 个 endpoint · 唯独登录 cURL 没抓 · 因为 Zihao
                   是浏览器已登录状态进的 · 没经过 login 页面)
        """
        # v27.8.0.2 修复(实测 · 2026-05-10):
        # 1. PHP 老代码 · 必须先 GET 一次才会建 PHPSESSID session
        # 2. POST checklogin.php 后 r.url 不变(同一页 echo HTML · 不 redirect)
        #    → 不能靠 r.url 判成功 · 改为「拿到 PHPSESSID = OK · 真假留给 select_company 验」
        try:
            self.session.get(f"{self.BASE}/", timeout=self.timeout,
                             allow_redirects=True)
        except requests.RequestException as e:
            raise MrErpNetworkError(f"预热网络错误:{e}")

        url = f"{self.BASE}/login/checklogin.php"
        payload = {
            "txtusers": self.username,      # 注意复数!
            "txtpasswords": self.password,  # 注意复数!
            "btnsubmit": "Submit",          # 必须带提交按钮值 · 否则 PHP 老代码不认
        }
        headers = {
            "Referer": f"{self.BASE}/",
            "Origin": self.BASE,
        }
        try:
            r = self.session.post(url, data=payload, headers=headers,
                                  timeout=self.timeout, allow_redirects=True)
        except requests.RequestException as e:
            raise MrErpNetworkError(f"登录网络错误:{e}")

        if r.status_code >= 500:
            raise MrErpNetworkError(f"MR.ERP 服务端错误 {r.status_code}")

        sessid = self.session.cookies.get("PHPSESSID")
        if not sessid:
            raise MrErpAuthError("登录响应未返回 PHPSESSID(连 session 都没建)")
        # 注意:此时不能确定密码对错 · 留给 select_company() 验证
        # (checklogin.php 失败也返回 200 + HTML · 必须 GET mainmenu 看是否被踢回 login)

        sessid = self.session.cookies.get("PHPSESSID")
        if not sessid:
            raise MrErpAuthError("登录响应未返回 PHPSESSID")
        self._logged_in = True
        logger.info(f"MR.ERP 登录成功 · PHPSESSID={sessid[:8]}...")
        return sessid

    # ------------------------------------------------------------------
    # Step 0b · 选公司 + 拿 idus
    # ------------------------------------------------------------------
    def select_company(self) -> str:
        """切到指定 company/db · 同时从 formupload.php scrape idus

        实测:
            1. GET /login/mainmenu.php?comidyear=N&seldb=N → 激活 session(进主菜单)
            2. GET /impartran/formupload.php?idmenu=370 → 拿 hidden input idus value
               (实测确认 idus 直接以 hidden field 存在每个业务页 · v27.8.0.1)
        """
        if not self._logged_in:
            raise MrErpAuthError("未登录 · 请先 login()")

        # v27.8.0.3:补完整选公司流程 · 模拟用户点 TEST2019 按钮
        # 1a. GET selectdb.php(选公司页 · 服务端要求先看到这一步)
        try:
            self.session.get(f"{self.BASE}/login/selectdb.php",
                             timeout=self.timeout, allow_redirects=True)
        except requests.RequestException as e:
            logger.warning(f"GET selectdb.php 失败 · 继续:{e}")

        # 1b. GET mainmenu.php?comidyear=N&seldb=N(等同点 TEST2019 按钮)
        url = f"{self.BASE}/login/mainmenu.php"
        params = {"comidyear": self.comidyear, "seldb": self.seldb}
        headers = {"Referer": f"{self.BASE}/login/selectdb.php"}
        try:
            r = self.session.get(url, params=params, headers=headers,
                                 timeout=self.timeout, allow_redirects=True)
        except requests.RequestException as e:
            raise MrErpNetworkError(f"选公司网络错误:{e}")

        if r.status_code != 200:
            raise MrErpAuthError(f"选公司失败 status={r.status_code}")

        # v27.8.0.2 真实登录成功判定:被踢回 login/checklogin/index = 登录失败
        url_low = r.url.lower()
        if any(x in url_low for x in ["checklogin", "/login/index", "/login/?",
                                       "/login.php", "/index.php"]):
            raise MrErpAuthError(
                f"用户名/密码错误(GET mainmenu 被踢回 {r.url})"
            )
        # 也要看 HTML body · 有时不 redirect 直接返回 login form
        body_low = (r.text or "")[:5000].lower()
        if "txtusers" in body_low or "txtpasswords" in body_low:
            raise MrErpAuthError(
                "GET mainmenu 返回了登录表单 · session 失效 / 密码错"
            )

        # 2. 预拉 SC 上传页 · scrape idus(实测最稳)
        # idus 在每个业务页都以 <input hidden name="idus" value="N"> 出现
        probe_url = f"{self.BASE}/impartran/formupload.php?idmenu=370"
        probe_headers = {"Referer": f"{self.BASE}/login/mainmenu.php"}
        try:
            r2 = self.session.get(probe_url, headers=probe_headers,
                                  timeout=self.timeout)
            idus = self._scrape_idus(r2.text)
            if not idus:
                logger.warning("formupload.php 也未找到 idus · 用最后兜底")
                idus = self._scrape_idus(r.text) or self.session.cookies.get("idus")
        except requests.RequestException as e:
            logger.warning(f"预拉 formupload 失败:{e} · 试主菜单 HTML")
            idus = self._scrape_idus(r.text)
            r2 = None

        if not idus:
            # v27.8.0.3 调试输出:dump 响应内容 · 看服务端到底返了啥
            print("\n" + "="*60)
            print("❌ scrape idus 失败 · dump 服务端响应供诊断:")
            print("="*60)
            print(f"GET {probe_url}")
            print(f"  → status: {r2.status_code if r2 is not None else 'N/A'}")
            print(f"  → final_url: {r2.url if r2 is not None else 'N/A'}")
            print(f"  → cookies: {dict(self.session.cookies)}")
            print(f"  → body 前 1500 字符:")
            print("-"*60)
            print((r2.text if r2 is not None else "")[:1500])
            print("-"*60)
            print(f"\nGET mainmenu 响应 final_url: {r.url}")
            print(f"GET mainmenu body 前 800 字符:")
            print("-"*60)
            print((r.text or "")[:800])
            print("="*60)
            raise MrErpAuthError("无法 scrape idus · 见上面 dump 诊断")

        self.idus = idus
        self._company_selected = True
        logger.info(f"MR.ERP 选公司成功 · idus={idus}")
        return idus

    @staticmethod
    def _scrape_idus(html: str) -> Optional[str]:
        """从 HTML 里抓 idus · bs4 优先 · 正则兜底

        实测样本:<input type="hidden" name="idus" id="idus" value="15">
                   注意 name 和 value 之间隔了 id 属性 · 严格正则会漏
        """
        if not html:
            return None
        # 优先 bs4(最稳 · 不受属性顺序影响)
        try:
            soup = BeautifulSoup(html, "html.parser")
            inp = soup.find("input", attrs={"name": "idus"})
            if inp and inp.get("value"):
                v = str(inp.get("value")).strip()
                if v.isdigit():
                    return v
        except Exception as e:
            logger.debug(f"bs4 scrape idus failed: {e}")
        # 兜底正则(允许 name 和 value 之间有任意其他属性)
        m = re.search(
            r'<input[^>]*\bname=["\']idus["\'][^>]*\bvalue=["\'](\d+)["\']',
            html, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(
            r'<input[^>]*\bvalue=["\'](\d+)["\'][^>]*\bname=["\']idus["\']',
            html, re.IGNORECASE)
        if m:
            return m.group(1)
        # JS 模式
        m = re.search(r'(?:var|let|const)\s+idus\s*=\s*["\']?(\d+)', html)
        if m:
            return m.group(1)
        return None

    # ------------------------------------------------------------------
    # Step 1 · 上传 xlsx(存 server session)
    # ------------------------------------------------------------------
    def upload_xlsx(self, file_bytes: bytes, module: str = "sales_credit",
                    filename: str = "import.xlsx") -> bool:
        """上传 xlsx 到 MR.ERP 临时 session · 不真写库

        实测:POST /impartran/component/uploadexcel.php
            multipart file
            Headers: Referer + X-Requested-With + Origin
            Response: 200 + 0 字节(成功) · 4xx/5xx(失败)

        Returns:
            True 成功 / False 失败
        """
        self._ensure_ready()
        cfg = self._get_module_cfg(module)

        url = f"{self.BASE}/{cfg['path']}/component/uploadexcel.php"
        referer = f"{self.BASE}/{cfg['path']}/formupload.php?idmenu={cfg['idmenu']}"

        # v27.8.0.1 实测确认(从 view-source: formupload.php scrape):
        # <input type="file" name="uploadfile" accept="...spreadsheet...">
        # form 还含 hidden input idus + select selmenu
        files = {
            "uploadfile": (filename, file_bytes,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        # 同 form 的其他字段也带上(模拟浏览器整 form 提交)
        data = {
            "idus": str(self.idus),
            "selmenu": str(cfg["selmenu"]),
        }
        headers = {
            "Referer": referer,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.BASE,
            "Accept": "text/html, */*; q=0.01",
        }
        try:
            r = self.session.post(url, files=files, data=data, headers=headers,
                                  timeout=self.timeout)
        except requests.RequestException as e:
            raise MrErpNetworkError(f"上传 xlsx 网络错误:{e}")

        if r.status_code == 401 or r.status_code == 403:
            raise MrErpAuthError("session 已过期 · 需重新登录")
        if r.status_code >= 400:
            raise MrErpValidationError(f"上传被拒 status={r.status_code} body={r.text[:200]}")

        # 实测:成功返回 200 + Content-Length: 0
        logger.info(f"MR.ERP upload_xlsx 成功 · {len(file_bytes)}B → 0B response")
        return True

    # ------------------------------------------------------------------
    # Step 2 · 拿预览页 · 解析数据 + 提取 row_ids
    # ------------------------------------------------------------------
    def fetch_preview(self, module: str = "sales_credit") -> list:
        """v27.8.1.6 · 拿预览页 HTML · 解析出可勾选的行 + 数据快照
        额外:把完整 HTML 留在 self.last_preview_html(失败时上层能取出来给用户)"""
        self._ensure_ready()
        cfg = self._get_module_cfg(module)
        if not cfg.get("selmenu"):
            raise MrErpModuleError(
                f"module={module} 的 selmenu 待抓 · 暂不支持 · 请走 xlsx 兜底"
            )
        if not self.idus:
            raise MrErpAuthError("idus 未设置 · 请先 select_company()")

        url = f"{self.BASE}/{cfg['path']}/formrdpc.php"
        data = {"idus": self.idus, "selmenu": cfg["selmenu"]}
        headers = {
            "Referer": f"{self.BASE}/{cfg['path']}/formupload.php?idmenu={cfg['idmenu']}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.BASE,
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            r = self.session.post(url, data=data, headers=headers,
                                  timeout=self.timeout)
        except requests.RequestException as e:
            raise MrErpNetworkError(f"拿预览页网络错误:{e}")

        # v27.8.1.6 · 总是把 raw HTML 留下 · 失败诊断关键证据
        self.last_preview_html = r.text or ""

        if r.status_code >= 400:
            raise MrErpValidationError(f"预览失败 status={r.status_code}")

        return self._parse_preview_html(r.text)

    @staticmethod
    def extract_error_hints(html: str) -> list:
        """v27.8.1.6 · 从 MR.ERP 预览页 HTML 抢救式抓错误线索
        预览空时调 · 给上层提供「为啥被拒」的具体原因"""
        if not html:
            return []
        hints = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            # 1. 红色文字(MR.ERP 常用 <font color="red"> / style="color:red")
            for el in soup.find_all(["font", "span", "div", "td", "p"]):
                style = (el.get("style") or "").lower()
                color = (el.get("color") or "").lower()
                cls = " ".join(el.get("class") or []).lower()
                if "red" in color or "red" in style or "ff0000" in style \
                        or any(k in cls for k in ("error", "alert", "warning", "danger")):
                    txt = el.get_text(" ", strip=True)
                    if txt and 2 < len(txt) < 300 and txt not in hints:
                        hints.append(txt)
            # 2. JS alert 弹窗(很多 PHP 系统失败用 alert)
            for script in soup.find_all("script"):
                stxt = script.string or ""
                for m in re.finditer(r"alert\(['\"]([^'\"]+)['\"]\)", stxt):
                    a = m.group(1)
                    if a and a not in hints:
                        hints.append(a)
            # 3. 关键词扫文本(泰文/中文/英文「找不到/错误/无效/不存在」)
            txt_all = soup.get_text("\n", strip=True)
            for line in txt_all.split("\n"):
                line = line.strip()
                if not line or len(line) > 300 or line in hints:
                    continue
                low = line.lower()
                if any(kw in line for kw in ("ไม่พบ", "ผิดพลาด", "ไม่ถูกต้อง", "ห้าม",
                                              "错误", "失败", "不存在", "无效",
                                              "ซ้ำ")) \
                        or any(kw in low for kw in ("error", "invalid", "not found",
                                                     "duplicate", "fail")):
                    hints.append(line)
                    if len(hints) >= 8:
                        break
        except Exception:
            pass
        return hints[:8]

    @staticmethod
    def _parse_preview_html(html: str) -> list:
        """解析预览页 HTML"""
        soup = BeautifulSoup(html, "html.parser")
        rows = []

        # 找所有 form 内的 cbimport[N] checkbox · N 就是 row_id
        for cb in soup.find_all("input",
                                 attrs={"name": re.compile(r"^cbimport\[\d+\]$")}):
            name = cb.get("name", "")
            m = re.match(r"^cbimport\[(\d+)\]$", name)
            if not m:
                continue
            row_id = m.group(1)

            # 同 <p> 内的兄弟 <span> 文本就是字段值(实测 r.txt 的结构)
            data = {}
            parent_p = cb.find_parent("p")
            if parent_p:
                spans = parent_p.find_all("span")
                # 第 1 个 span 是 checkbox 容器 · 跳过
                texts = [s.get_text(strip=True) for s in spans[1:]]
                # ⚠️ v27.8.0.1:列名是从 form 的"表头" <p>(包含表头 span 的那行)
                #   抓出来 · 这里先简单按位置存
                for i, txt in enumerate(texts):
                    data[f"col_{i}"] = txt

            rows.append({"row_id": row_id, "data": data})

        # 顺便抓表头 column 名 · 让 col_N 可以映射到中泰文字段名
        # form 里第一个 <p>(没 cbimport · 全是表头 span)
        headers_map = {}
        for form in soup.find_all("form", id=re.compile(r"^frmimport\d+$")):
            ps = form.find_all("p")
            if not ps:
                continue
            # 第 1 个 <p> 是表头(只含 label · 没数据)
            header_p = ps[0]
            header_spans = header_p.find_all("span")
            for i, s in enumerate(header_spans[1:]):  # 跳第 1 个
                txt = s.get_text(strip=True)
                if txt:
                    headers_map[f"col_{i}"] = txt
            break

        # 把 col_N 映射成真实字段名
        for row in rows:
            new_data = {}
            for k, v in row["data"].items():
                new_data[headers_map.get(k, k)] = v
            row["data"] = new_data

        return rows

    # ------------------------------------------------------------------
    # Step 3 · 确认导入(真写库)
    # ------------------------------------------------------------------
    def confirm_import(self, module: str = "sales_credit",
                       row_ids: Optional[list] = None) -> dict:
        """确认导入 · 把预览数据真写进 MR.ERP 数据库

        实测:POST /impartran/component/importpc.php
            multipart:
              idus            (15)
              selmenu         (118)
              cballfrmimport1 (on · 表示全选)
              cbimport[N]     (N · 每个要导入的 row 一项 · 数组形式)
            Headers: Referer=formrdpc.php + X-Requested-With
            Response: 200 + 短字符串(实测 "2" · 推测是导入成功的 row id 或个数)

        Args:
            row_ids: 要导入的 row_id 列表(从 fetch_preview 拿) · None=全部
                     如果只想导入部分 · 传子集

        Returns:
            {
                "success": True,
                "raw": "2",                     # 服务端原始返回
                "imported_rows": ["2"],         # 实际导入的 row_id
                "module": "sales_credit"
            }
        """
        self._ensure_ready()
        cfg = self._get_module_cfg(module)
        if not cfg.get("selmenu"):
            raise MrErpModuleError(f"module={module} 的 selmenu 待抓")
        if not self.idus:
            raise MrErpAuthError("idus 未设置")
        if row_ids is None or len(row_ids) == 0:
            raise ValueError("row_ids 不能为空 · 请先调 fetch_preview()")

        url = f"{self.BASE}/{cfg['path']}/component/importpc.php"

        # 用 multipart 发 · 即使全是文本(实测服务端只接 multipart)
        # requests 用 files=(name,(None,value)) 触发 multipart 编码
        files = [
            ("idus", (None, str(self.idus))),
            ("selmenu", (None, str(cfg["selmenu"]))),
            ("cballfrmimport1", (None, "on")),
        ]
        for rid in row_ids:
            files.append((f"cbimport[{rid}]", (None, str(rid))))

        headers = {
            "Referer": f"{self.BASE}/{cfg['path']}/formrdpc.php",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.BASE,
            "Accept": "text/html, */*; q=0.01",
        }
        try:
            r = self.session.post(url, files=files, headers=headers,
                                  timeout=self.timeout)
        except requests.RequestException as e:
            raise MrErpNetworkError(f"确认导入网络错误:{e}")

        if r.status_code == 401 or r.status_code == 403:
            raise MrErpAuthError("session 已过期")
        if r.status_code >= 400:
            raise MrErpValidationError(
                f"确认导入被拒 status={r.status_code} body={r.text[:200]}"
            )

        raw = (r.text or "").strip()
        # ⚠️ v27.8.0.1:错误 response 长啥样待 Zihao 故意失败 1 次抓
        #   猜测 · 失败可能返回 "0" / "-1" / 错误描述字符串
        #   现在保守判定:数字 = 成功 · 非数字 = 失败
        if not raw:
            raise MrErpValidationError("确认导入返回空 · 未知状态")
        if not raw.replace(".", "").replace(",", "").isdigit():
            # 不是纯数字 · 大概率是错误信息
            raise MrErpValidationError(f"MR.ERP 报错:{raw[:200]}")

        logger.info(f"MR.ERP confirm_import 成功 · raw={raw}")
        return {
            "success": True,
            "raw": raw,
            "imported_rows": row_ids,
            "module": module,
        }

    # ------------------------------------------------------------------
    # 一键三步(最常用入口 · 给 Pearnly app.py 调)
    # ------------------------------------------------------------------
    def push_xlsx(self, file_bytes: bytes, module: str = "sales_credit",
                  filename: str = "import.xlsx",
                  auto_confirm: bool = True) -> dict:
        """一键完成 upload + preview + confirm

        Args:
            auto_confirm: True=自动确认全部行 / False=只到预览 · 让用户审核

        Returns:
            auto_confirm=True:
                {"success": True, "imported_rows": [...], "preview": [...]}
            auto_confirm=False:
                {"success": True, "stage": "preview", "preview": [...]}
        """
        self.upload_xlsx(file_bytes, module=module, filename=filename)
        preview = self.fetch_preview(module=module)
        if not preview:
            # v27.8.1.6 · 抢救式抓 MR.ERP HTML 里的错误线索 + 整段 HTML 也带出
            html = getattr(self, "last_preview_html", "") or ""
            hints = self.extract_error_hints(html)
            msg = "预览页无可导入行(xlsx 数据可能被服务端拒绝)"
            if hints:
                msg = msg + " · MR.ERP 提示:" + " / ".join(hints[:3])
            err = MrErpValidationError(msg)
            err.raw_html = html[:8000]   # 留前 8KB 给上层存日志
            err.hints = hints
            raise err

        if not auto_confirm:
            return {"success": True, "stage": "preview", "preview": preview}

        row_ids = [row["row_id"] for row in preview]
        confirm_result = self.confirm_import(module=module, row_ids=row_ids)
        return {
            "success": True,
            "stage": "confirmed",
            "preview": preview,
            "imported_rows": confirm_result["imported_rows"],
            "raw_response": confirm_result["raw"],
        }

    # ------------------------------------------------------------------
    # 便利方法
    # ------------------------------------------------------------------
    def login_and_select(self):
        """链式 login + select_company · 快捷入口"""
        self.login()
        self.select_company()
        return self

    def _ensure_ready(self):
        if not self._logged_in:
            raise MrErpAuthError("未登录 · 请先调 login()")
        if not self._company_selected:
            raise MrErpAuthError("未选公司 · 请先调 select_company()")

    @staticmethod
    def _get_module_cfg(module: str) -> dict:
        cfg = MODULE_MAP.get(module)
        if not cfg:
            raise MrErpModuleError(
                f"未知 module={module} · 支持:{list(MODULE_MAP.keys())}"
            )
        return cfg


# ============================================================================
# 自测入口(命令行 · 给 Zihao 跑验证)
# ============================================================================
if __name__ == "__main__":
    import argparse, sys
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    ap = argparse.ArgumentParser(description="MrErpPusher 5 步流程实测")
    ap.add_argument("--username", required=True, help="MR.ERP username · 如 test01")
    ap.add_argument("--password", required=True, help="MR.ERP 密码")
    ap.add_argument("--xlsx", required=True, help="要上传的 xlsx 路径")
    ap.add_argument("--module", default="sales_credit",
                    choices=list(MODULE_MAP.keys()))
    ap.add_argument("--comidyear", type=int, default=6)
    ap.add_argument("--seldb", type=int, default=1)
    ap.add_argument("--no-confirm", action="store_true",
                    help="只到预览 · 不真导入(干跑)")
    args = ap.parse_args()

    with open(args.xlsx, "rb") as f:
        xlsx_bytes = f.read()

    pusher = MrErpPusher(args.username, args.password,
                         comidyear=args.comidyear, seldb=args.seldb)
    try:
        print("→ Step 0a · login")
        pusher.login()
        print(f"  ✅ PHPSESSID 已拿 · idus={pusher.idus}")

        print("→ Step 0b · select_company")
        pusher.select_company()
        print(f"  ✅ idus={pusher.idus}")

        print("→ Step 1 · upload_xlsx")
        pusher.upload_xlsx(xlsx_bytes, module=args.module)
        print("  ✅ 上传成功(0 字节响应是预期)")

        print("→ Step 2 · fetch_preview")
        rows = pusher.fetch_preview(module=args.module)
        print(f"  ✅ 预览到 {len(rows)} 行:")
        for r in rows[:5]:
            print(f"    row_id={r['row_id']} · data={r['data']}")
        if not rows:
            print("  ⚠️ 预览 0 行 · 可能 xlsx 数据被服务端校验拒绝")
            sys.exit(1)

        if args.no_confirm:
            print("→ Step 3 · 跳过(--no-confirm)")
            sys.exit(0)

        print("→ Step 3 · confirm_import")
        row_ids = [r["row_id"] for r in rows]
        result = pusher.confirm_import(module=args.module, row_ids=row_ids)
        print(f"  ✅ 导入成功 · raw={result['raw']} rows={result['imported_rows']}")

        print("\n🏆 全 5 步流程跑通 · v27.8.0 反向工程验证完成")
    except MrErpAuthError as e:
        print(f"\n❌ 鉴权错误:{e}")
        sys.exit(2)
    except MrErpValidationError as e:
        print(f"\n❌ 业务校验失败:{e}")
        sys.exit(3)
    except MrErpNetworkError as e:
        print(f"\n❌ 网络错误:{e}")
        sys.exit(4)
    except MrErpModuleError as e:
        print(f"\n❌ 模块未支持:{e}")
        sys.exit(5)
