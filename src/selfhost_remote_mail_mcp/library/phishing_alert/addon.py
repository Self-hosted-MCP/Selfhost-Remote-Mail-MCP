# SPDX-License-Identifier: AGPL-3.0-only
"""Phishing alert: warns about signs of a scam in an email: failed sender checks, lookalike domains, links that hide where they go, risky files."""

import io
import ipaddress
import re
import zipfile
from email.utils import getaddresses, parseaddr
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

# Brands that phishing often pretends to be: the brand word -> the domain names it really uses.
BRANDS = {
    "paypal": {"paypal", "paypal-communication", "paypalobjects"},
    "apple": {"apple", "icloud", "me", "mac", "itunes"},
    "icloud": {"apple", "icloud", "me", "mac"},
    "microsoft": {"microsoft", "outlook", "live", "office", "office365", "microsoftonline", "onmicrosoft",
                  "sharepoint", "hotmail", "msn", "windows", "azure", "bing", "skype", "xbox"},
    "google": {"google", "gmail", "googlemail", "youtube", "withgoogle", "googleusercontent", "gstatic"},
    "gmail": {"google", "gmail", "googlemail"},
    "amazon": {"amazon", "amazonses", "a2z", "amazonaws", "aws"},
    "netflix": {"netflix", "nflxext", "nflximg"},
    "dhl": {"dhl", "dpdhl", "dhl-news"},
    "fedex": {"fedex"},
    "docusign": {"docusign"},
    "dropbox": {"dropbox", "dropboxmail"},
    "linkedin": {"linkedin", "lnkd"},
    "facebook": {"facebook", "facebookmail", "fb", "meta", "metamail"},
    "instagram": {"instagram", "facebookmail", "meta"},
    "whatsapp": {"whatsapp", "facebookmail", "meta"},
    "coinbase": {"coinbase"},
    "binance": {"binance"},
    "ebay": {"ebay"},
    "spotify": {"spotify"},
    "adobe": {"adobe", "adobesign", "echosign"},
    "wetransfer": {"wetransfer"},
    "metamask": {"metamask", "consensys"},
    "ledger": {"ledger"},
    "trust wallet": {"trustwallet"},
    "cpanel": {"cpanel"},
}
WORDS = {"apple", "amazon", "adobe", "spotify", "dropbox", "ledger", "trust wallet"}   # brands that are also ordinary words: exact matches only
SERVICES = {"zoho", "zohomail", "google", "messagingengine", "fastmail", "cloudflare", "namecheap", "godaddy",
            "porkbun", "hostinger", "ionos", "ovh", "privateemail", "github", "vercel", "netlify", "gandi", "squarespace",
            "wix", "shopify", "mailgun", "postmarkapp", "sendgrid", "amazonses", "migadu", "purelymail", "proton"}
FREEMAIL = {"gmail", "googlemail", "outlook", "hotmail", "live", "msn", "yahoo", "ymail", "icloud", "me", "mac",
            "proton", "protonmail", "pm", "gmx", "web", "mail", "aol", "zoho", "yandex", "fastmail", "tutanota",
            "tuta", "hey", "qq", "163", "126", "naver", "libero", "orange", "free", "laposte", "t-online"}
# Providers whose own "Authentication-Results" lines can be trusted, by their domain name.
PROVIDER_CHECKERS = {"google", "icloud", "apple", "messagingengine", "fastmail", "yahoo", "yahoodns", "zoho",
                     "zohomail", "outlook", "protection", "microsoft", "proton", "protonmail", "gmx", "web", "aol",
                     "mailbox", "posteo", "migadu", "mxroute", "purelymail", "titan", "hostinger", "ionos", "ovh"}
PROGRAMS = {"exe", "scr", "js", "jse", "vbs", "vbe", "bat", "cmd", "ps1", "jar", "msi", "lnk", "iso", "img", "com",
            "pif", "hta", "wsf", "wsh", "cpl", "one", "xll", "vhd", "vhdx", "reg", "dll", "apk", "app", "dmg", "pkg"}
MACROS = {"docm", "xlsm", "pptm", "xlam", "dotm", "xltm", "potm", "ppam", "xlsb"}
WEB_FILES = {"html", "htm", "shtml", "svg", "xhtml", "mht", "mhtml"}
REDIRECTS = {"safelinks.protection.outlook.com": "url", "google.com": "q", "l.facebook.com": "u",
             "lm.facebook.com": "u", "l.instagram.com": "u", "linkprotect.cudasvc.com": "a"}
SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "edu", "or", "ne", "go", "gob", "nic"}
CONFUSABLE = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "4": "a", "а": "a", "е": "e", "о": "o",
                            "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d",
                            "ο": "o", "α": "a", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ρ": "p", "τ": "t", "υ": "u"})
LEVELS = {"high": 0, "medium": 1, "low": 2}


def short(text: str, n: int = 60) -> str:
    """Something the sender wrote, made safe to show: no control characters, cut short, in quotes."""
    text = "".join(ch for ch in str(text) if ch.isprintable()).strip()
    return f"\"{text[:n]}{'…' if len(text) > n else ''}\""


def domain_of(address: str) -> str:
    return address.rsplit("@", 1)[-1].strip().strip(".").lower() if "@" in address else ""


def name_of(domain: str) -> str:
    """The domain's own name, without subdomains or the ending: mail.paypal.co.uk -> paypal."""
    labels = [x for x in domain.lower().strip(".").split(".") if x]
    if len(labels) >= 3 and len(labels[-1]) == 2 and labels[-2] in SECOND_LEVEL:
        return labels[-3]
    return labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")


def decoded(domain: str) -> str:
    try:
        return domain.encode().decode("idna") if "xn--" in domain else domain
    except UnicodeError:
        return domain


def mixed_script(text: str) -> bool:
    latin = any("a" <= ch <= "z" for ch in text.lower())
    other = any("Ͱ" <= ch <= "Ͽ" or "Ѐ" <= ch <= "ӿ" for ch in text)
    return latin and other


def lookalike(name: str, targets: set[str]) -> str:
    """The target a domain name imitates with lookalike letters (paypa1, rnicrosoft, Cyrillic а), or a brand
    used as a part of it (paypal-secure), or ""."""
    if not name or name in targets:
        return ""
    skeleton = name.translate(CONFUSABLE).replace("rn", "m").replace("vv", "w")
    for target in targets:
        if skeleton == target:
            return target
        parts = re.split(r"[-_]", skeleton)
        if len(parts) > 1 and len(target) >= 5 and target not in WORDS and target in parts:
            return target
    return ""


def clean_host(host: str) -> str:
    """A host name safe to show: letters, digits, dots and dashes only, else "a hidden address"."""
    host = (host or "").lower()
    return host if re.fullmatch(r"[a-z0-9.-]{1,80}", host) else "a hidden address"


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[list[str]] = []
        self._open = None

    def handle_starttag(self, tag, attrs):
        if tag == "a" and len(self.links) < 300:
            self._open = [dict(attrs).get("href") or "", ""]

    def handle_data(self, data):
        if self._open is not None:
            self._open[1] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._open is not None:
            self.links.append(self._open)
            self._open = None


def unwrap(href: str) -> str:
    """The real address behind well-known link wrappers (Outlook Safe Links, Google, Facebook)."""
    for _ in range(3):
        parts = urlparse(href)
        host = (parts.hostname or "").lower()
        key = next((k for d, k in REDIRECTS.items() if host == d or host.endswith("." + d)), None)
        if not key or key not in parse_qs(parts.query):
            break
        href = unquote(parse_qs(parts.query)[key][0])
    return href


VISIBLE_URL = re.compile(r"^\s*(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})(?:[/:?#]\S*)?\s*$", re.I)


def setup(api):
    def own_names() -> set[str]:
        try:
            names = {name_of(domain_of(a)) for a in api.mailboxes()}
        except Exception:
            names = set()
        return {n for n in names if n and n not in FREEMAIL}

    def auth_results(msg) -> dict | None:
        return api.sender_checks(msg)

    def findings(msg) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        add = lambda level, text: out.append((level, text))
        display, sender = parseaddr(str(msg.get("From", "")))
        sender_domain = clean_host(domain_of(sender))
        sender_name = name_of(sender_domain)
        auth = auth_results(msg) or {}
        dmarc_pass = auth.get("dmarc") == "pass"
        mine = own_names()
        brands = set(BRANDS)

        # 0. The user's provider already thinks it's spam
        folder = str(getattr(msg, "mail_folder", "")).split(":")[-1].lower()
        if folder in ("spam", "junk", "junk email", "junk e-mail", "bulk mail", "[gmail]/spam") or \
                (msg.get("X-Spam-Flag") or "").strip().lower() == "yes" or \
                str(msg.get("X-Spam-Status") or "").lower().startswith("yes"):
            add("high", "Your provider put this email in Spam.")

        # 1. Sender checks done by the user's own provider
        if auth.get("dmarc") == "fail":
            add("high", f"The sender failed your provider's DMARC check: it may not really come from {sender_domain}.")
        elif not dmarc_pass and (auth.get("spf") in ("fail",) or auth.get("dkim") in ("fail",)):
            add("low", "One of your provider's sender checks failed (SPF or DKIM). This also happens with forwarded mail and mailing lists.")

        # 2. Display name tricks
        own_full = {a.lower() for a in api.mailboxes()}
        own_domains = {domain_of(a) for a in own_full} - {""}
        if display and sender.lower() not in own_full and sender_domain not in own_domains:
            low = display.lower()
            hit = next((d for d in own_domains if d in low and name_of(d) not in FREEMAIL), None)
            service = sender_name in SERVICES or any(sender_name in v for v in BRANDS.values())
            if hit and not (dmarc_pass and service):   # your mail or domain provider writing about your domain is fine
                add("high", f"The name pretends to be {hit}, but it comes from {sender_domain}.")
            if mixed_script(display):
                add("high", f"The name {short(display, 40)} mixes alphabets to look like someone else.")
        if display:
            shown = re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", display)
            if shown and all(s.lower() != sender.lower() for s in shown):
                add("medium", f"The name shows the address {short(shown[0], 50)}, but the email really comes from {short(sender, 50)}.")
            for brand in brands:
                if re.search(rf"\b{brand}\b", display, re.I) and sender_name not in BRANDS[brand] and sender_name not in mine:
                    add("low" if dmarc_pass else "medium",
                        f"The name says {short(display, 40)}, but it comes from {sender_domain}, not {brand.capitalize()}.")
                    break

        # 3. Lookalike domains, for the sender and the reply address
        reply = parseaddr(str(msg.get("Reply-To", "")))[1]
        for label, address in (("sender", sender), ("reply address", reply)):
            dom = domain_of(address)
            if not dom:
                continue
            name = name_of(decoded(dom))
            if mixed_script(decoded(dom)):
                add("high", f"The {label}'s domain {short(decoded(dom), 50)} mixes alphabets to look like another site.")
                continue
            if name in FREEMAIL:
                continue
            target = lookalike(name, mine) or (lookalike(name, brands) if name not in {n for v in BRANDS.values() for n in v} else "")
            if target:
                whose = "your own domain" if target in mine else f"{target.capitalize()}"
                add("medium" if dmarc_pass else "high", f"The {label}'s domain {clean_host(dom)} imitates {whose}.")

        # 4. Reply address
        reply_name = name_of(domain_of(reply))
        if reply and reply_name and reply_name != sender_name and reply_name in FREEMAIL and sender_name not in FREEMAIL:
            add("medium", f"Replies would go to a personal address ({short(reply, 50)}), not to {sender_domain}.")

        # 5. Links
        html_part = msg.get_body(preferencelist=("html",))
        if html_part is not None:
            try:
                parser = Links()
                parser.feed(html_part.get_content()[:500_000])
            except Exception:
                parser = None
            newsletter = dmarc_pass and msg.get("List-Unsubscribe")
            hidden = set()
            for href, text in parser.links if parser else []:
                try:
                    real = unwrap(href.strip())
                    host = (urlparse(real).hostname or "").lower()
                except ValueError:
                    continue   # a broken link address: skip it
                if not host:
                    continue
                try:
                    ip = ipaddress.ip_address(host)
                    if not ip.is_global:
                        add("low", f"A link goes to a local network address ({clean_host(host)}).")
                    else:
                        add("high", f"A link goes to a bare internet address ({clean_host(host)}), not a named site.")
                    continue
                except ValueError:
                    pass
                if mixed_script(decoded(host)):
                    add("medium", f"A link goes to {short(decoded(host), 50)}, which mixes alphabets.")
                visible = VISIBLE_URL.match(" ".join(text.split()))
                if not visible:
                    continue
                shown_name, real_name = name_of(visible.group(1)), name_of(host)
                if shown_name == real_name or real_name in hidden:
                    continue
                if shown_name in mine or any(shown_name in v for v in BRANDS.values()):
                    hidden.add(real_name)
                    add("high", f"A link shows {short(visible.group(1), 40)} but goes to {clean_host(host)}.")
                elif not newsletter:
                    hidden.add(real_name)
                    add("low", f"A link shows {short(visible.group(1), 40)} but goes to {clean_host(host)} (often tracking).")

        # 6. Attachments
        for part in msg.iter_attachments():
            fname = str(part.get_filename() or "")
            if not fname or (part.get_content_disposition() == "inline" and part.get_content_maintype() == "image"):
                continue
            exts = [e.lower() for e in fname.split(".")[1:]]
            last = exts[-1] if exts else ""
            if last in PROGRAMS:
                twice = len(exts) >= 2 and exts[-2] in {"pdf", "doc", "docx", "xls", "xlsx", "jpg", "png", "txt", "zip"}
                add("high", f"The attachment {short(fname, 50)} is a program" + (" pretending to be a document." if twice else "."))
            elif last in WEB_FILES:
                add("medium", f"The attachment {short(fname, 50)} is a web page; fake login pages often come this way.")
            elif last in MACROS:
                add("medium", f"The attachment {short(fname, 50)} can contain macros (small programs).")
            elif last == "zip":
                try:
                    data = part.get_payload(decode=True) or b""
                    inside = zipfile.ZipFile(io.BytesIO(data)).infolist() if len(data) < 25_000_000 else []
                except Exception:
                    inside = []
                inner = [i.filename.rsplit(".", 1)[-1].lower() for i in inside[:200] if "." in i.filename]
                if any(e in PROGRAMS for e in inner):
                    add("high", f"The zip {short(fname, 50)} holds a program.")
                elif any(e in WEB_FILES for e in inner):
                    add("high", f"The zip {short(fname, 50)} holds a web page, a common way to hide a fake login page.")
                elif any(i.flag_bits & 1 for i in inside):
                    add("medium", f"The zip {short(fname, 50)} is password-protected, so mail scanners can't look inside.")
        out.sort(key=lambda f: LEVELS[f[0]])
        return out[:12]

    def trust(msg) -> tuple[str, str, list]:
        """A simple trust level for an email: high, medium or low, and the main reason in a few words."""
        found = findings(msg)
        if any(level == "high" for level, _ in found):
            return "low", found[0][1], found
        if any(level == "medium" for level, _ in found):
            return "medium", found[0][1], found
        return "high", "", found

    @api.tool(api.READ)
    def check_email(email_id: str, details: bool = False) -> str:
        """Check one email for signs of phishing or a scam. Answers in one line: a trust level (high, medium or
        low) and the main reason. details=true lists every warning sign. Nothing is fetched or sent."""
        level, reason, found = trust(api.message(email_id))
        line = f"Trust: {level}." + (f" {reason}" if reason else " No warning signs found.")
        if not details or not found:
            return line
        return "\n".join([line] + [f"- {lvl}: {txt}" for lvl, txt in found])

    def note(msg):
        level, reason, _found = trust(msg)
        return f"phishing check, trust {level}: {reason}" if level != "high" else None

    api.on_read(note)
