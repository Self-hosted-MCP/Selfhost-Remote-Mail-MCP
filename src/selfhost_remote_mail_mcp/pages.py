"""The server's web pages: the login page AI apps open, and the settings page.

Plain HTML and CSS, no scripts, no fonts or images from anywhere else (see HEADERS), so the pages work under a
strict Content-Security-Policy. Light and dark follow the device. Every value put into a page goes through
esc() first. The logic behind the pages (sessions, CSRF, saving) lives in server.py.
"""

from __future__ import annotations

import html
import re
import string

PROJECT = "Selfhost-Remote-Mail-MCP"
PROJECT_URL = "https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP"
AUTHOR = "s17sh70x2jfl031ag"

# Never cached, never shown inside another site, never telling other sites where you came from.
HEADERS = {
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
                               "form-action 'self' https: http://localhost:* http://127.0.0.1:*; frame-ancestors 'none'; base-uri 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}

MODE_LABELS = {"full": "Full", "draft": "Draft only", "read": "Read only"}
MODE_HELP = {"full": "read, draft, sort and send", "draft": "read, draft and sort, never send",
             "read": "read and search only"}

esc = html.escape

ICON_MAIL = ('<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M4 9.5A2.5 2.5 0 0 1 6.5 7h19A2.5 2.5 0 0 1 28 '
             '9.5v13a2.5 2.5 0 0 1-2.5 2.5h-19A2.5 2.5 0 0 1 4 22.5z"/><path d="m5 9 11 8.5L27 9"/></svg>')
ICON_SHIELD = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
               'stroke-linejoin="round" aria-hidden="true"><path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z"/>'
               '<path d="M12 8v5"/><path d="M12 16.5v.01"/></svg>')
ICON_ALERT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5"/>'
              '<path d="M12 16.5v.01"/></svg>')
ICON_CHECK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.6 2.6L16 9.5"/></svg>')

# The envelope mark, as the favicon and the icon AI apps may show next to this server.
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#5546ea"/>
<g fill="none" stroke="#fff" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 21a4 4 0 0 1 4-4h32a4 4 0 0 1 4 4v22a4 4 0 0 1-4 4H16a4 4 0 0 1-4-4z"/><path d="m14 20 18 14 18-14"/></g></svg>"""

CSS = """
:root{--brand:#5546ea;--brand-deep:#4536d2;--on-brand:#fff;--on-brand-soft:#e4e0ff;--page:#f1f0f8;--card:#fff;
--ink:#16142a;--ink-soft:#4d4a66;--line:#cdcae0;--line-soft:#e6e4f1;--field:#fff;--error:#b42318;--error-bg:#fdecea;
--ok:#12703f;--ok-bg:#e5f5ec;--chip:#efedff;--chip-ink:#4536d2;--warn:#8a4b00;--warn-bg:#fff3d6;
--lime:#c8f53a;--lime-ink:#1d2600;--pink:#ffb6d5;--pink-ink:#8c2357;
--shadow:0 18px 40px -18px rgba(30,20,80,.35),0 2px 6px rgba(30,20,80,.08)}
@media (prefers-color-scheme:dark){:root{--brand:#6a5cff;--brand-deep:#5a4bf0;--page:#0f0e17;--card:#181725;
--ink:#efeef8;--ink-soft:#aba8c4;--line:#37344c;--line-soft:#28263a;--field:#0f0e17;--error:#ff8f80;--error-bg:#3a1c1a;
--ok:#6fd49b;--ok-bg:#143022;--chip:#28244a;--chip-ink:#c6bfff;--warn:#ffc46b;--warn-bg:#3a2a10;
--lime:#d4ff4f;--lime-ink:#1d2600;--pink:#ffc4de;--pink-ink:#ffc4de;
--shadow:0 18px 40px -18px rgba(0,0,0,.7),0 2px 6px rgba(0,0,0,.4)}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--page);color:var(--ink);
font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
display:flex;flex-direction:column;align-items:center;padding:clamp(0px,6vh,72px) 0 32px}
main{width:100%;max-width:440px;background:var(--card);box-shadow:var(--shadow);overflow:clip}
main.wide{max-width:760px}
@media (min-width:480px){main{border-radius:22px}}
@media (max-width:479px){body{padding:0 0 28px;background:var(--card)}main{box-shadow:none}}
.hero{background:var(--brand);color:var(--on-brand);padding:28px 28px 32px}
.mark{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:-.01em;color:var(--on-brand-soft)}
.mark::after{content:"";width:7px;height:7px;border-radius:2px;background:var(--pink);margin-left:-2px}
.hl{background:linear-gradient(transparent 62%,var(--lime) 62%,var(--lime) 92%,transparent 92%);color:var(--on-brand);padding:0 .04em}
.hero .hl{background:linear-gradient(transparent 58%,var(--lime) 58%,var(--lime) 90%,transparent 90%);color:var(--on-brand);
text-shadow:1px 0 0 var(--brand-deep),-1px 0 0 var(--brand-deep),0 1px 0 var(--brand-deep),0 -1px 0 var(--brand-deep),
1px 1px 0 var(--brand-deep),-1px 1px 0 var(--brand-deep),1px -1px 0 var(--brand-deep),-1px -1px 0 var(--brand-deep),0 0 4px var(--brand-deep)}
.tabs{position:sticky;top:0;z-index:2;display:flex;gap:4px;overflow-x:auto;padding:10px 20px;background:color-mix(in srgb,var(--card) 92%,transparent);
backdrop-filter:saturate(1.4) blur(10px);-webkit-backdrop-filter:saturate(1.4) blur(10px);border-bottom:1.5px solid var(--line-soft);scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs a{flex:none;color:var(--ink-soft);text-decoration:none;font-weight:700;font-size:.9rem;padding:7px 13px;border-radius:999px;transition:background .15s,color .15s}
.tabs a:hover,.tabs a:focus-visible{background:var(--lime);color:var(--lime-ink);outline:none}
section[id],h2[id]{scroll-margin-top:72px}
.mark svg{width:30px;height:30px;flex:none}
.mark path{stroke-dasharray:90;stroke-dashoffset:0;animation:draw .8s cubic-bezier(.16,1,.3,1) both}
@keyframes draw{from{stroke-dashoffset:90}}
@media (prefers-reduced-motion:reduce){.mark path{animation:none}}
h1{margin:44px 0 10px;font-size:clamp(2rem,8vw,2.6rem);line-height:1.05;letter-spacing:-.035em;font-weight:800;text-wrap:balance}
.hero p{margin:0;color:var(--on-brand-soft);font-size:1.02rem;max-width:46ch}
.hero b{color:var(--on-brand);font-weight:650}
.body{padding:28px}
h2{font-size:1.2rem;letter-spacing:-.02em;margin:40px 0 4px;display:flex;align-items:center;gap:9px}
h2::before{content:"";width:6px;height:6px;border-radius:2px;background:var(--pink);flex:none}
h2:first-child{margin-top:0}
.lead{margin:0 0 16px;color:var(--ink-soft)}
label{display:block;font-weight:650;margin:0 0 8px}
input,select{width:100%;font:inherit;font-size:1.02rem;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);
background:var(--field);color:var(--ink);transition:border-color .15s}
input:focus,select:focus{outline:3px solid color-mix(in srgb,var(--brand) 35%,transparent);outline-offset:1px;border-color:var(--brand)}
button{font:inherit;font-weight:700;font-size:1.02rem;padding:13px 18px;border:0;border-radius:12px;background:var(--brand);
color:var(--on-brand);cursor:pointer;box-shadow:0 8px 18px -10px var(--brand);transition:background .15s,transform .1s}
button:hover{background:var(--brand-deep)}
button:active{transform:translateY(1px)}
button:focus-visible,summary:focus-visible{outline:3px solid color-mix(in srgb,var(--brand) 45%,transparent);outline-offset:3px}
button.block{width:100%;margin-top:14px}
button.quiet{background:transparent;color:var(--ink);border:1.5px solid var(--line);box-shadow:none;font-weight:650;padding:9px 14px;font-size:.95rem}
button.quiet:hover{border-color:var(--ink-soft);background:transparent}
button.danger{background:transparent;color:var(--error);border:1.5px solid color-mix(in srgb,var(--error) 45%,transparent);box-shadow:none;padding:9px 14px;font-size:.95rem}
button.danger:hover{background:var(--error-bg)}
.msg{display:flex;gap:10px;align-items:flex-start;margin:0 0 18px;padding:12px 14px;border-radius:12px;font-weight:600}
.msg svg{width:20px;height:20px;flex:none;margin-top:2px}
.msg.error{background:var(--error-bg);color:var(--error)}
.msg.ok{background:var(--ok-bg);color:var(--ok)}
.msg.tip{background:var(--warn-bg);color:var(--warn)}
.msg b{margin-right:4px}
.note{display:flex;gap:10px;margin:22px 0 0;color:var(--ink-soft);font-size:.92rem}
.note svg{width:18px;height:18px;flex:none;margin-top:3px}
.steps{margin:0;padding-left:20px;color:var(--ink-soft)}
.steps li{margin:6px 0}
fieldset{border:0;margin:0 0 18px;padding:0}
legend{font-weight:650;margin-bottom:8px;padding:0}
.choice{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1.5px solid var(--line);border-radius:12px;margin:0 0 8px;cursor:pointer;font-weight:500}
.choice:has(input:checked){border-color:var(--brand);background:color-mix(in srgb,var(--brand) 7%,transparent)}
.choice input{width:20px;height:20px;margin:0;accent-color:var(--brand);flex:none}
.choice span.addr{flex:1;min-width:0;overflow-wrap:anywhere}
.badge{display:inline-block;font-size:.78rem;font-weight:700;letter-spacing:.02em;padding:3px 9px;border-radius:999px;background:var(--chip);color:var(--chip-ink);white-space:nowrap}
.badge.read{background:var(--line-soft);color:var(--ink-soft)}
.badge.lime{background:var(--lime);color:var(--lime-ink)}
b .badge,.item-head .badge{margin-left:6px;vertical-align:1px}
.badge.fail{background:var(--error-bg);color:var(--error)}
.list{border:1.5px solid var(--line-soft);border-radius:16px;overflow:hidden}
.item{padding:16px 18px;border-top:1.5px solid var(--line-soft)}
.item:first-child{border-top:0}
.item-head{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}
.item-head b{overflow-wrap:anywhere}
.muted{color:var(--ink-soft);font-size:.9rem}
.actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.actions form{margin:0}
details{margin-top:12px}
summary{cursor:pointer;font-weight:650;color:var(--brand);list-style:none;display:inline-block}
@media (prefers-color-scheme:dark){summary{color:var(--chip-ink)}}
summary::-webkit-details-marker{display:none}
summary::after{content:" +";font-weight:700}
details[open] summary::after{content:" \\2013"}
.grid{display:grid;gap:14px;margin-top:14px}
@media (min-width:560px){.grid.two{grid-template-columns:1fr 1fr}}
.hint{font-weight:400;color:var(--ink-soft);font-size:.88rem;margin:6px 0 0}
.confirm{display:flex;gap:10px;align-items:center;font-weight:500;margin:10px 0}
.confirm input{width:18px;height:18px;margin:0;accent-color:var(--error)}
.remember{margin:14px 0 0}
.remember input{accent-color:var(--brand)}
.empty{padding:22px 18px;color:var(--ink-soft)}
.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-top:34px;padding-top:22px;border-top:1.5px solid var(--line-soft)}
.changelog{margin-top:8px;color:var(--ink-soft);font-size:.95rem}
.changelog h3{color:var(--ink);font-size:1rem;margin:18px 0 6px}
.changelog ul{padding-left:20px;margin:0}
.changelog li{margin:4px 0}
code{font-size:.9em;background:var(--line-soft);padding:1px 5px;border-radius:5px}
.lead a{color:inherit}
.drop{display:block;border:2px dashed var(--line);border-radius:16px;padding:22px 18px;text-align:center;cursor:pointer;
transition:border-color .15s,background .15s}
.drop:hover,.drop:focus-within{border-color:var(--brand);background:color-mix(in srgb,var(--brand) 5%,transparent)}
.drop svg{width:34px;height:34px;color:var(--brand);display:block;margin:0 auto 8px}
@media (prefers-color-scheme:dark){.drop svg{color:var(--chip-ink)}}
.drop b{display:block;font-size:1.05rem}
.drop input{margin-top:14px;border:0;padding:0;background:none;font-size:.95rem;color:var(--ink-soft)}
.drop input::file-selector-button{font:inherit;font-weight:650;margin-right:12px;padding:9px 14px;border-radius:10px;
border:1.5px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.file-row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.file-row .grow{flex:1;min-width:180px}
.file-row b{display:block;overflow-wrap:anywhere}
.warn{display:flex;gap:10px;align-items:flex-start;margin:12px 0 0;padding:10px 12px;border-radius:12px;
background:var(--warn-bg);color:var(--warn);font-size:.92rem;font-weight:600}
.warn svg{width:18px;height:18px;flex:none;margin-top:2px}
.say{margin:18px 0 0;padding:14px 16px;border-radius:14px;background:var(--chip);color:var(--ink)}
.say q{font-weight:650}
.bar a{color:var(--ink-soft);font-weight:650;text-underline-offset:3px}
footer{margin-top:22px;font-size:.85rem;color:var(--ink-soft);text-align:center;padding:0 16px}
footer a{color:inherit;text-underline-offset:3px;text-decoration-color:var(--pink)}
"""

PAGE = string.Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex,nofollow">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<title>$title</title>
<style>$css</style></head>
<body><main class="$width">
<section class="hero">
<div class="mark">$icon Selfhost Mail</div>
<h1>$headline</h1>
<p>$sub</p>
</section>
$tabs<section class="body">$content</section>
</main>
<footer><a href="$project_url">$project</a> by $author</footer>
</body></html>""")


def page(headline: str, sub: str, content: str, wide: bool = False, tabs: list[tuple[str, str]] | None = None) -> str:
    """headline and sub may hold simple markup, so callers escape what they put in. tabs: (anchor, label) links
    to the page's sections, shown under the header and kept in view while scrolling."""
    nav = ('<nav class="tabs" aria-label="Sections">' + "".join(f'<a href="#{a}">{esc(t)}</a>' for a, t in tabs)
           + "</nav>") if tabs else ""
    title = re.sub(r"<[^>]+>", "", headline)
    return PAGE.substitute(title=f"{title} · Selfhost Mail", headline=headline, sub=sub, content=content, tabs=nav,
                           css=CSS, icon=ICON_MAIL, width="wide" if wide else "", project=PROJECT,
                           project_url=PROJECT_URL, author=AUTHOR)


def message(kind: str, text: str) -> str:
    """kind: 'error' or 'ok'. text is escaped here."""
    icon = ICON_ALERT if kind == "error" else ICON_CHECK
    role = ' role="alert"' if kind == "error" else ' role="status"'
    return f'<p class="msg {kind}"{role}>{icon}<span>{esc(text)}</span></p>'


def who(address: str, name: str = "") -> str:
    """'Work' over 'work@example.com', or just the address."""
    if not name:
        return esc(address)
    return f'<b>{esc(name)}</b> <span class="muted">{esc(address)}</span>'


def badge(mode: str) -> str:
    return f'<span class="badge {mode}">{MODE_LABELS.get(mode, mode)}</span>'


def mode_options(selected: str) -> str:
    return "".join(f'<option value="{m}"{" selected" if m == selected else ""}>{MODE_LABELS[m]}</option>'
                   for m in MODE_LABELS)


MODE_HINT = ('<p class="hint">Full: read, draft, sort and send. Draft only: everything but sending. '
             'Read only: read and search.</p>')


# ---------------------------------------------------------------- login page (AI apps connecting)

def login(app: str | None, host: str | None, req: str, mailboxes: list[tuple[str, str, str]], error: str = "",
          expired_text: str = "", settings_url: str = "") -> str:
    """mailboxes: (address, mode, name) for every mailbox the server knows."""
    if app is None:
        steps = ('<ol class="steps"><li>Go back to your AI app.</li><li>Start connecting the mail server again.</li>'
                 '<li>A fresh login page opens. It stays valid for 10 minutes.</li></ol>')
        return page("This login link has expired", esc(expired_text or "Login links last 10 minutes."), steps)
    if len(mailboxes) > 1:
        boxes = "".join(
            f'<label class="choice"><input type="checkbox" name="mailbox" value="{esc(addr)}" checked>'
            f'<span class="addr">{who(addr, name)}</span>{badge(mode)}</label>' for addr, mode, name in mailboxes)
        choose = (f'<fieldset><legend>Which mailboxes may {esc(app)} use?</legend>{boxes}'
                  '<p class="hint">Each mailbox keeps its own limits: a read-only one stays read-only.</p></fieldset>')
    elif mailboxes:
        choose = f'<input type="hidden" name="mailbox" value="{esc(mailboxes[0][0])}">'
    else:
        choose = message("error", "No mailbox is set up on this server yet. Add one first.")
    if any(mode == "full" for _addr, mode, _name in mailboxes):
        choose += ('<fieldset><legend>Sending</legend><label class="choice"><input type="checkbox" name="allow_send" '
                   f'value="yes"><span class="addr">Allow {esc(app)} to send email</span></label>'
                   f'<p class="hint"><b>Not ticked:</b> {esc(app)} writes drafts, and you press send yourself in your '
                   f'mail app.<br><b>Ticked:</b> {esc(app)} can also press send for you. Tip: set sending to "ask '
                   'first" in your AI app.</p></fieldset>')
    local = (host or "").lower() in ("localhost", "127.0.0.1", "::1")
    warn = message("error", f"{app} returns to an app on a computer (localhost). Only continue if that's your own "
                            "computer and you just started this connection there.") if local else ""
    content = (f'{message("error", error) if error else ""}{warn}<form method="post" action="/login">'
               f'<input type="hidden" name="req" value="{esc(req)}">{choose}'
               '<label for="passphrase">Passphrase</label>'
               '<input id="passphrase" type="password" name="passphrase" autocomplete="current-password" autofocus required>'
               '<button class="block" type="submit">Allow access</button></form>'
               f'<p class="note">{ICON_SHIELD}<span>Only continue if you started this connection yourself, just now. '
               'Otherwise close this page: nothing happens without your passphrase.</span></p>'
               + (f'<p class="note">{ICON_CHECK}<span>Afterwards, manage everything (mailboxes, apps, privacy, files) '
                  f'at <b>{esc(settings_url)}</b>, with the same passphrase.</span></p>' if settings_url else ''))
    return page(f'{esc(app)} wants your <span class="hl">mailbox</span>', f"After you allow it, you go back to <b>{esc(host or '?')}</b>.", content)


# ---------------------------------------------------------------- settings page

ICON_UPLOAD = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
               'stroke-linejoin="round" aria-hidden="true"><path d="M12 15V4"/><path d="m7 9 5-5 5 5"/>'
               '<path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>')


def settings_login(error: str = "", after: str = "/settings") -> str:
    files = after == "/settings/upload"
    content = (f'{message("error", error) if error else ""}<form method="post" action="/settings/login">'
               f'<input type="hidden" name="next" value="{esc(after)}">'
               '<label for="passphrase">Passphrase</label>'
               '<input id="passphrase" type="password" name="passphrase" autocomplete="current-password" autofocus required>'
               '<label class="confirm remember"><input type="checkbox" name="remember" value="yes" checked>'
               'Remember this device for 90 days</label>'
               f'<button class="block" type="submit">{"Open files" if files else "Open settings"}</button></form>'
               f'<p class="note">{ICON_SHIELD}<span>Same passphrase as when you connect an AI app. Let your phone or '
               'browser save it, so next time it fills in by itself. Untick "Remember" on a shared computer. Five '
               'wrong tries lock this page for 15 minutes.</span></p>')
    if files:
        return page("Files for your emails", "Upload a photo or document, then ask your AI app to attach it.", content)
    return page("Settings", "Your mailboxes and the AI apps that may use them.", content)


def _csrf(token: str) -> str:
    return f'<input type="hidden" name="csrf" value="{esc(token)}">'


def _post(action: str, csrf: str, fields: dict[str, str], label: str, cls: str = "quiet", extra: str = "") -> str:
    hidden = "".join(f'<input type="hidden" name="{esc(k)}" value="{esc(v)}">' for k, v in fields.items())
    return f'<form method="post" action="{action}">{_csrf(csrf)}{hidden}{extra}<button class="{cls}" type="submit">{label}</button></form>'


def _host_fields(prefix: str, imap_host: str = "", imap_port: str = "993", smtp_host: str = "", smtp_port: str = "465",
                 username: str = "", smtp_username: str = "") -> str:
    return (f'<div class="grid two">'
            f'<div><label for="{prefix}ih">IMAP server</label><input id="{prefix}ih" name="imap_host" value="{esc(imap_host)}" placeholder="imap.example.com"></div>'
            f'<div><label for="{prefix}ip">IMAP port</label><input id="{prefix}ip" name="imap_port" value="{esc(imap_port)}" inputmode="numeric"></div>'
            f'<div><label for="{prefix}sh">SMTP server</label><input id="{prefix}sh" name="smtp_host" value="{esc(smtp_host)}" placeholder="smtp.example.com"></div>'
            f'<div><label for="{prefix}sp">SMTP port</label><input id="{prefix}sp" name="smtp_port" value="{esc(smtp_port)}" inputmode="numeric"></div>'
            f'<div><label for="{prefix}un">Login name <span class="hint">if not the address</span></label><input id="{prefix}un" name="username" value="{esc(username)}" autocomplete="off"></div>'
            f'<div><label for="{prefix}su">Login name for sending <span class="hint">rarely needed</span></label><input id="{prefix}su" name="smtp_username" value="{esc(smtp_username)}" autocomplete="off"></div>'
            '</div>')


def settings(csrf: str, mailboxes: list[dict], apps: list[dict], flash: tuple[str, str] | None, max_boxes: int,
             server_read_only: bool, about: dict | None = None, uploads_on: bool = False,
             devices: dict | None = None, privacy: list[dict] | None = None, changes: list[dict] | None = None) -> str:
    """mailboxes: dicts with address, mode, source, name, imap_host, imap_port, smtp_host, smtp_port, username,
    smtp_username. apps: dicts with client_id, name, host, grant (list or None)."""
    if flash and flash[0] == "domain":
        icons = {"good": ("ok", ICON_CHECK), "warn": ("tip", ICON_ALERT), "bad": ("error", ICON_ALERT)}
        rows = "".join(f'<p class="msg {icons[level][0]}">{icons[level][1]}<span><b>{esc(name)}</b> {esc(text)}</span></p>'
                       for name, level, text in flash[1]["rows"])
        parts = [f'<h2>Domain check: {esc(flash[1]["address"].split("@")[1])}</h2><p class="lead">What other mail '
                 f'servers see when you send. Green is good.</p>{rows}']
    else:
        parts = [message(*flash) if flash else ""]
    if server_read_only:
        parts.append(message("error", "Read-only mode is on (MAIL_READ_ONLY=on): nothing can be changed or sent, "
                                      "whatever each mailbox's mode says."))

    # mailboxes
    parts.append('<h2 id="mailboxes">Mailboxes</h2><p class="lead">The first one is the default. Each mailbox keeps its own mode.</p>')
    if mailboxes:
        rows = []
        for i, m in enumerate(mailboxes):
            addr, web = m["address"], m["source"] == "web"
            where = "Added on this page" if web else "From the settings file. Change it there."
            row = [f'<div class="item"><div class="item-head">{who(addr, m["label"]) if m["label"] else f"<b>{esc(addr)}</b>"}'
                   f'{badge(m["mode"])}{"<span class=badge>Default</span>" if i == 0 else ""}</div>'
                   f'<div class="muted">{where} · {esc(MODE_HELP[m["mode"]])}</div><div class="actions">',
                   _post("/settings/mailbox", csrf, {"action": "test", "address": addr}, "Test login"),
                   _post("/settings/mailbox", csrf, {"action": "domain", "address": addr}, "Check domain")]
            row.append("</div>")
            row.append(f'<details><summary>Rename</summary><form method="post" action="/settings/mailbox">{_csrf(csrf)}'
                       f'<input type="hidden" name="action" value="rename"><input type="hidden" name="address" value="{esc(addr)}">'
                       f'<div class="grid"><div><label for="r{i}">Name for this mailbox <span class="hint">like Work or Personal. '
                       f'Leave empty to remove the name</span></label><input id="r{i}" name="label" value="{esc(m["label"])}" maxlength="40"></div></div>'
                       '<div class="actions"><button type="submit">Save name</button></div></form></details>')
            if web:
                edit = (f'<details><summary>Edit</summary><form method="post" action="/settings/mailbox">{_csrf(csrf)}'
                        f'<input type="hidden" name="action" value="update"><input type="hidden" name="address" value="{esc(addr)}">'
                        f'<div class="grid two"><div><label for="n{i}">Name on outgoing mail</label><input id="n{i}" name="name" value="{esc(m["name"])}"></div>'
                        f'<div><label for="m{i}">Mode</label><select id="m{i}" name="mode">{mode_options(m["mode"])}</select>{MODE_HINT}</div></div>'
                        f'<div class="grid"><div><label for="p{i}">New password <span class="hint">leave empty to keep the current one</span></label>'
                        f'<input id="p{i}" type="password" name="password" autocomplete="new-password"></div></div>'
                        + _host_fields(f"e{i}", m["imap_host"], str(m["imap_port"]), m["smtp_host"], str(m["smtp_port"]),
                                       m["username"], m["smtp_username"])
                        + '<div class="actions"><button type="submit">Save changes</button></div></form>'
                        + _post("/settings/mailbox", csrf, {"action": "delete", "address": addr}, "Remove mailbox", "danger",
                                '<label class="confirm"><input type="checkbox" name="confirm" value="yes" required>'
                                'Yes, remove it from this server. Its emails stay in the mailbox.</label>')
                        + "</details>")
                row.append(edit)
            row.append("</div>")
            rows.append("".join(row))
        parts.append(f'<div class="list">{"".join(rows)}</div>')
    else:
        parts.append('<div class="list"><p class="empty">No mailbox yet. Add the first one below.</p></div>')

    # add a mailbox
    if len(mailboxes) < max_boxes:
        parts.append(
            '<h2 id="add">Add a mailbox</h2><p class="lead">For Gmail, iCloud, Yahoo, Fastmail and other known providers the '
            'server names fill themselves in. Most of them need an app password.</p>'
            f'<form method="post" action="/settings/mailbox">{_csrf(csrf)}<input type="hidden" name="action" value="add">'
            '<div class="grid two">'
            '<div><label for="aa">Email address</label><input id="aa" type="email" name="address" required autocomplete="off"></div>'
            '<div><label for="al">Name for this mailbox <span class="hint">like Work</span></label><input id="al" name="label" maxlength="40" autocomplete="off"></div>'
            '<div><label for="an">Name on outgoing mail</label><input id="an" name="name" autocomplete="off"></div>'
            '<div><label for="ap">Password or app password</label><input id="ap" type="password" name="password" required autocomplete="new-password"></div>'
            f'<div><label for="am">Mode</label><select id="am" name="mode">{mode_options("draft")}</select>{MODE_HINT}</div>'
            '</div><details><summary>Server settings</summary><p class="hint">Only needed for providers that aren\'t '
            'filled in by themselves. See docs/email-providers.md.</p>' + _host_fields("a") + '</details>'
            '<div class="actions"><button type="submit">Test and add</button></div></form>')
    else:
        parts.append(f'<p class="lead">This server holds up to {max_boxes} mailboxes (MAX_MAILBOXES).</p>')

    # apps
    parts.append('<h2 id="apps">Connected apps</h2><p class="lead">AI apps that logged in, and the mailboxes each one may use.</p>')
    if apps:
        rows = []
        for i, a in enumerate(apps):
            grant = a["grant"]
            ticks = "".join(
                f'<label class="choice"><input type="checkbox" name="mailbox" value="{esc(m["address"])}"'
                f'{" checked" if grant is None or m["address"] in grant else ""}><span class="addr">{who(m["address"], m["label"])}</span>'
                f'{badge(m["mode"])}</label>' for m in mailboxes)
            rows.append(
                f'<div class="item"><div class="item-head"><b>{esc(a["name"])}</b><span class="muted">returns to {esc(a["host"])}</span></div>'
                f'<div class="muted">{"Every mailbox (connected before mailboxes could be chosen)" if grant is None else esc(", ".join(grant) or "No mailbox")}'
                f' · {"may send" if a["may_send"] else "may not send"}</div>'
                f'<details><summary>Choose mailboxes</summary><form method="post" action="/settings/app">{_csrf(csrf)}'
                f'<input type="hidden" name="action" value="grant"><input type="hidden" name="client_id" value="{esc(a["client_id"])}">'
                f'<fieldset style="margin-top:12px">{ticks}</fieldset>'
                f'<label class="choice"><input type="checkbox" name="allow_send" value="yes"{" checked" if a["may_send"] else ""}>'
                '<span class="addr">May send email</span></label>'
                '<div class="actions"><button type="submit">Save</button></div></form></details>'
                '<div class="actions">'
                + _post("/settings/app", csrf, {"action": "disconnect", "client_id": a["client_id"]}, "Disconnect", "danger")
                + "</div></div>")
        parts.append(f'<div class="list">{"".join(rows)}</div>')
    else:
        parts.append('<div class="list"><p class="empty">No app has connected yet.</p></div>')

    if uploads_on:
        parts.append('<h2 id="files">Files for your emails</h2><p class="lead">Upload a photo, PDF or document on '
                     '<a href="/settings/upload">the upload page</a>, then ask your AI app to attach it.</p>')

    if privacy is not None:
        parts.append('<h2 id="privacy">Privacy</h2><p class="lead">For files you attach from your computer, the AI or the upload '
                     'page. Files forwarded from other emails are left as they are.</p>')
        help_text = {"remove_photo_location": "Photos from phones often hold the exact place they were taken, and "
                                              "the camera. Works for jpg, png and webp; the photo itself isn't changed.",
                     "remove_document_details": "Word, Excel, PowerPoint, OpenDocument and PDF files often hold the "
                                                "author's name and company. Signed or locked PDFs are left alone."}
        rows = []
        for p in privacy:
            state = '<span class="badge lime">On</span>' if p["on"] else '<span class="badge read">Off</span>'
            if p["forced_off"]:
                button = '<span class="muted">Off in the server settings</span>'
            else:
                button = _post("/settings/privacy", csrf, {"name": p["name"], "action": "off" if p["on"] else "on"},
                               "Turn off" if p["on"] else "Turn on")
            rows.append(f'<div class="item"><div class="file-row"><div class="grow"><b>{esc(p["label"])} {state}</b>'
                        f'<span class="muted">{esc(help_text.get(p["name"], ""))}</span></div>{button}</div></div>')
        rows.append('<div class="item"><div class="file-row"><div class="grow"><b>No tracking <span class="badge lime">Always</span></b>'
                    '<span class="muted">The server never loads pictures or links inside emails, so senders can\'t '
                    'see when or where you read them.</span></div></div></div>')
        parts.append(f'<div class="list">{"".join(rows)}</div>')

    if devices is not None:
        parts.append('<h2 id="devices">Devices</h2><p class="lead">Browsers signed in to these pages. Sign out any you don\'t '
                     'recognise, then change your passphrase.</p>')
        rows = []
        for d in devices["list"]:
            name = esc(d["device"]) if d["device"] else "A device"
            facts = [f"Signed in {esc(d['since'])}" if d["since"] else "",
                     f"last seen {esc(d['seen'])}" if d["seen"] and not d["current"] else "",
                     f"from {esc(d['ip'])}" if d["ip"] else "",
                     "remembered for 90 days" if d["remember"] else "until the browser closes"]
            rows.append(
                f'<div class="item"><div class="file-row"><div class="grow"><b>{name}'
                + (' <span class="badge lime">This device</span>' if d["current"] else "")
                + f'</b><span class="muted">{" · ".join(f for f in facts if f)}</span></div>'
                + _post("/settings/device", csrf, {"action": "signout", "id": d["id"]}, "Sign out", "danger")
                + "</div></div>")
        parts.append(f'<div class="list">{"".join(rows)}</div>')
        if devices["on"]:
            parts.append('<h2 id="signins">Sign-ins, last 7 days</h2><p class="lead">Every passphrase try on these pages and '
                         'on AI app logins. A failed one you didn\'t make means someone is guessing.</p>')
            if devices["signins"]:
                events = "".join(
                    f'<div class="item"><div class="item-head"><b>{"Signed in" if e["ok"] else "Wrong passphrase"}</b>'
                    f'<span class="badge{"" if e["ok"] else " fail"}">{esc(e["where"])}</span></div>'
                    f'<div class="muted">{esc(e["time"])} · {esc(e["device"])} · from {esc(e["ip"])}</div></div>'
                    for e in devices["signins"][:50])
                parts.append(f'<div class="list">{events}</div>')
            else:
                parts.append('<div class="list"><p class="empty">No sign-ins in the last 7 days.</p></div>')
            parts.append('<div class="actions">' + _post("/settings/device", csrf, {"action": "log_off"},
                                                         "Turn off the device log") + '</div>'
                         '<p class="hint">Turning it off deletes this history and stops saving devices and network '
                         'addresses. Sign-ins keep working.</p>')
        elif devices.get("forced_off"):
            parts.append('<p class="lead">The device log is off (<code>DEVICE_LOG=off</code> in the server settings).</p>')
        else:
            parts.append('<p class="lead" style="margin-top:16px">The device log is off: no sign-in history or device '
                         'details are kept.</p><div class="actions">'
                         + _post("/settings/device", csrf, {"action": "log_on"}, "Turn on the device log") + "</div>")

    if changes is not None:
        parts.append('<h2 id="changes">Changes by AI apps</h2><p class="lead">Settings an AI app changed because you '
                     'asked it to, in the last 30 days. AI apps can only change photo location, document details, '
                     'the update check, your signature, templates and uploaded files.</p>')
        if changes:
            rows = "".join(f'<div class="item"><div class="item-head"><b>{esc(c["what"].splitlines()[0])}</b></div>'
                           f'<div class="muted">{esc(c["time"])} · {esc(c["app"])}</div></div>' for c in changes[:50])
            parts.append(f'<div class="list">{rows}</div>')
        else:
            parts.append('<div class="list"><p class="empty">No changes by AI apps.</p></div>')

    if about:
        upd = about.get("update")
        if upd is None:
            status = ('Update checks are off. Ask your AI app to turn them on, or set <code>UPDATE_CHECK=on</code>, to be told about new releases '
                      '(the server then asks GitHub once a day which version is newest, and sends nothing else).')
        elif upd["newer"]:
            status = (f'<b>Update available: {esc(upd["latest"])}</b>. <a href="{esc(upd["url"])}">What\'s new</a> · '
                      f'<a href="{PROJECT_URL}/blob/main/docs/updates.md">How to update</a>')
        else:
            status = "Up to date." + (f' Newest release: {esc(upd["latest"])}.' if upd["latest"] else "")
        parts.append(f'<h2 id="about">About this server</h2><p class="lead">Version <b>{esc(about["version"])}</b>. {status}</p>')
        if about.get("addons"):
            parts.append(f'<p class="lead">Add-ons: <b>{esc(", ".join(about["addons"]))}</b>.</p>')
        if about.get("changelog"):
            parts.append(f'<details><summary>What\'s new</summary><div class="changelog">{about["changelog"]}</div></details>')
    parts.append('<div class="bar"><span class="muted">Changes count right away. Apps never see mail passwords.</span>'
                 + _post("/settings/logout", csrf, {}, "Sign out") + "</div>")
    tabs = [("mailboxes", "Mailboxes"), ("apps", "Apps"), ("files", "Files") if uploads_on else None,
            ("privacy", "Privacy") if privacy is not None else None, ("devices", "Devices") if devices is not None else None,
            ("changes", "AI changes") if changes is not None else None,
            ("about", "About") if about else None]
    return page('Selfhost Mail <span class="hl">MCP</span>', "Mailboxes, modes, and which AI apps may use them.",
                "".join(parts), wide=True, tabs=[t for t in tabs if t])


# ---------------------------------------------------------------- upload page

def uploads(csrf: str, files: list[dict], flash: tuple[str, str] | None, max_size: str, accept: str) -> str:
    """files: dicts with code, name, size_text, level, why, used, minutes_left (newest first)."""
    parts = [message(*flash) if flash else ""]
    parts.append(
        f'<form method="post" action="/settings/upload" enctype="multipart/form-data">{_csrf(csrf)}'
        f'<label class="drop">{ICON_UPLOAD}<b>Choose a file</b>'
        f'<span class="muted">Photos, PDFs, documents, audio, video or zip. Up to {esc(max_size)}.</span>'
        f'<input type="file" name="file" accept="{esc(accept)}" required></label>'
        '<button class="block" type="submit">Upload</button></form>')
    parts.append('<h2 style="margin-top:34px">Waiting to be attached</h2>')
    if files:
        rows = []
        for f in files:
            mins = f["minutes_left"]
            left = f"{mins} min" if mins < 60 else f"{round(mins / 60)} h"
            status = (f"In a draft · deleted in {left}" if f["used"] else f"Not used yet · deleted in {left}")
            warn = (f'<p class="warn">{ICON_ALERT}<span>Check this: {esc(f["why"])}. Your AI app will ask you '
                    'before attaching it.</span></p>') if f["level"] == "suspect" else ""
            rows.append(
                f'<div class="item"><div class="file-row">'
                f'<div class="grow"><b>{esc(f["name"])}</b><span class="muted">{esc(f["size_text"])} · {status} · '
                f'code {esc(f["code"])}</span></div>'
                + _post("/settings/upload", csrf, {"action": "delete", "code": f["code"]}, "Delete", "danger")
                + f'</div>{warn}</div>')
        parts.append(f'<div class="list">{"".join(rows)}</div>')
        parts.append(f'<p class="say">Then tell your AI app: <q>Attach the file I just uploaded to the email to Sam.</q> '
                     f'Or use its name: <q>Attach {esc(files[0]["name"])}.</q></p>')
    else:
        parts.append('<div class="list"><p class="empty">Nothing here. Uploaded files show up here with their code.</p></div>')
    parts.append(f'<p class="note">{ICON_SHIELD}<span>Files are stored encrypted. Each one is deleted 1 hour after it '
                 'first goes into a draft, or after 24 hours if it\'s never used. Your emails keep their own copy. '
                 'Programs and scripts are always refused.</span></p>')
    parts.append('<div class="bar"><a href="/settings">Back to settings</a>' + _post("/settings/logout", csrf, {}, "Sign out")
                 + "</div>")
    return page('Files for your <span class="hl">emails</span>', "Upload a file, then ask your AI app to attach it.",
                "".join(parts), wide=True)
