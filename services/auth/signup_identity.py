"""注册身份归一化与网络来源工具。"""

from fastapi import Request

DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com",
    "tempmail.net",
    "10minutemail.com",
    "10minutemail.net",
    "guerrillamail.com",
    "guerrillamail.net",
    "guerrillamail.org",
    "mailinator.com",
    "mailinator.net",
    "mailinator.org",
    "throwawaymail.com",
    "yopmail.com",
    "yopmail.net",
    "yopmail.fr",
    "trashmail.com",
    "trashmail.net",
    "trashmail.de",
    "fakeinbox.com",
    "sharklasers.com",
    "grr.la",
    "guerrillamailblock.com",
    "mintemail.com",
    "tempinbox.com",
    "spambox.us",
    "spam4.me",
    "mailcatch.com",
    "maildrop.cc",
    "mailnesia.com",
    "getairmail.com",
    "getnada.com",
    "inboxkitten.com",
    "mvrht.com",
    "tempmailaddress.com",
    "temp-mail.org",
    "temp-mail.io",
    "tempr.email",
    "dispostable.com",
    "discard.email",
    "discardmail.com",
    "moakt.com",
    "tempemail.co",
    "fakemail.net",
    "fakemailgenerator.com",
    "throwaway.email",
    "burnermail.io",
    "emailondeck.com",
    "harakirimail.com",
    "spamgourmet.com",
    "deadaddress.com",
    "anonbox.net",
    "spamcorptastic.com",
    "spamfree24.org",
    "armyspy.com",
    "cuvox.de",
    "dayrep.com",
    "einrot.com",
    "fleckens.hu",
    "gustr.com",
    "jourrapide.com",
    "rhyta.com",
    "superrito.com",
    "teleworm.us",
    "mohmal.com",
    "mailtothis.com",
    "mytemp.email",
}


def normalize_email(email: str) -> str:
    """
    邮箱归一化(防 + alias 和点号绕过)
    a+1@gmail.com → a@gmail.com
    a.b@gmail.com → ab@gmail.com
    """
    if not email or "@" not in email:
        return (email or "").lower().strip()
    local, _, domain = email.lower().strip().partition("@")
    domain = domain.strip()
    if "+" in local:
        local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def is_disposable_email(email: str) -> bool:
    """检测临时邮箱。"""
    if not email or "@" not in email:
        return False
    domain = email.lower().split("@", 1)[1].strip()
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return True
    parts = domain.split(".")
    for i in range(len(parts)):
        sub = ".".join(parts[i:])
        if sub in DISPOSABLE_EMAIL_DOMAINS:
            return True
    return False


def get_client_ip_safe(request: Request) -> str:
    """取真实 IP(过 Cloudflare)。"""
    headers = request.headers
    ip = headers.get("cf-connecting-ip") or headers.get("x-forwarded-for") or ""
    if ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        try:
            ip = request.client.host
        except Exception:
            ip = "unknown"
    return ip


def get_ip_subnet24(ip: str) -> str:
    """取 IPv4 /24 网段。"""
    try:
        if ":" in ip:
            return ip
        parts = ip.split(".")
        if len(parts) != 4:
            return ip
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return ip
