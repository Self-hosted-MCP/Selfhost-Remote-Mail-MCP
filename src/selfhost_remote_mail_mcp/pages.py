# SPDX-License-Identifier: AGPL-3.0-only
"""The server's web pages: the login page AI apps open, and the settings page.

Plain HTML and CSS, no scripts, no fonts or images from anywhere else (see HEADERS), so the pages work under a
strict Content-Security-Policy. Light and dark follow the device, unless the visitor picked one (a cookie). Every value put into a page goes through
esc() first. The logic behind the pages (sessions, CSRF, saving) lives in server.py.
"""

from __future__ import annotations

import contextvars
import html
import re
import string

from .i18n import LANG, LANGUAGES, N_, _

PROJECT = "Selfhost-Remote-Mail-MCP"
PROJECT_URL = "https://github.com/s17sh70x2jfl031ag/Selfhost-Remote-Mail-MCP"
AUTHOR = "s17sh70x2jfl031ag"

# Never cached, never shown inside another site, never telling other sites where you came from.
HEADERS = {
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; "
                               "img-src 'self' data: https://github.com https://avatars.githubusercontent.com; "
                               "form-action 'self' https: http://localhost:* http://127.0.0.1:*; frame-ancestors 'none'; base-uri 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}

MODE_LABELS = {"full": N_("Full"), "draft": N_("Draft only"), "read": N_("Read only")}
MODE_HELP = {"full": N_("read, draft, sort and send"), "draft": N_("read, draft and sort, never send"),
             "read": N_("read and search only")}
PRIVACY_HELP = {
    "remove_photo_location": N_("Photos from phones often hold the exact place they were taken, and the camera. Works "
                                "for jpg, png and webp; the photo itself isn't changed."),
    "remove_document_details": N_("Word, Excel, PowerPoint, OpenDocument and PDF files often hold the author's name "
                                  "and company. Signed or locked PDFs are left alone."),
    "upload_links": N_("Lets an AI app upload a file you dropped into the chat, with a one-time link (one file, 10 "
                       "minutes). Off: you upload files yourself on the upload page."),
}
ADDON_HELP = {   # the library add-ons, in words for the settings page (others show their own description)
    "calendar_invite": N_("Attaches a calendar invite to a draft, so the receiver adds the meeting in one tap."),
    "pdf_maker": N_("Turns text with headings, lists and tables into a PDF and attaches it to a draft."),
    "invoices": N_("Makes numbered quotes, proformas and invoices as PDFs, with the totals worked out."),
    "phishing_alert": N_("Gives each email a trust level and warns your AI app about likely scams."),
    "follow_ups": N_("Tells you which emails you sent got no reply in time."),
    "out_of_office": N_("While you're away, answers new emails with your message, once per person. Sends by itself."),
    "caldav": N_("Your calendar: see events, find free times and add events (iCloud, Fastmail, Nextcloud and others)."),
    "webhooks": N_("Tells a web address of yours when new mail arrives: sender, subject and date, never the email itself."),
}
ADDON_TITLES = {"calendar_invite": N_("Calendar invite"), "pdf_maker": N_("PDF maker"),
                "invoices": N_("Invoices and quotes"), "phishing_alert": N_("Phishing alert"),
                "follow_ups": N_("Follow-up reminders"), "out_of_office": N_("Out of office"),
                "caldav": N_("Calendar"), "webhooks": N_("Webhooks")}
LIBRARY_URL = f"{PROJECT_URL}/tree/main/src/selfhost_remote_mail_mcp/library"


def addon_title(name: str) -> str:
    return _(ADDON_TITLES[name]) if name in ADDON_TITLES else name

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

_svg = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">')
THEME_ICONS = {   # what the button shows: the look now
    "": _svg + '<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor" stroke="none"/></svg>',
    "light": _svg + '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2'
             'M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/></svg>',
    "dark": _svg + '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/></svg>',
}
THEME_LABELS = {"": N_("Light or dark: like your device. Tap to change."), "light": N_("Light. Tap to change."),
                "dark": N_("Dark. Tap to change.")}
SOURCE_URL = contextvars.ContextVar("source_url", default="")   # a changed version's source code (AGPL), if set
THEME = contextvars.ContextVar("theme", default="")      # "", "light" or "dark", from the visitor's cookie
HERE_PATH = contextvars.ContextVar("here", default="/")  # the page's own address, to come back to after a tap


def theme_button() -> str:
    t = THEME.get()
    label = esc(_(THEME_LABELS.get(t, THEME_LABELS[""])))
    return (f'<form class="theme" method="post" action="/theme"><input type="hidden" name="next" '
            f'value="{esc(HERE_PATH.get())}"><button type="submit" title="{label}" aria-label="{label}">'
            f'{THEME_ICONS.get(t, THEME_ICONS[""])}</button></form>')


ICON_STAR = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" '
             'aria-hidden="true"><path d="m12 3.5 2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.8l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg>')
ICON_BACK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>')
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
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--brand:#6a5cff;--brand-deep:#5a4bf0;--page:#0f0e17;--card:#181725;
--ink:#efeef8;--ink-soft:#aba8c4;--line:#37344c;--line-soft:#28263a;--field:#0f0e17;--error:#ff8f80;--error-bg:#3a1c1a;
--ok:#6fd49b;--ok-bg:#143022;--chip:#28244a;--chip-ink:#c6bfff;--warn:#ffc46b;--warn-bg:#3a2a10;
--lime:#d4ff4f;--lime-ink:#1d2600;--pink:#ffc4de;--pink-ink:#ffc4de;
--shadow:0 18px 40px -18px rgba(0,0,0,.7),0 2px 6px rgba(0,0,0,.4)}}
:root[data-theme=dark]{--brand:#6a5cff;--brand-deep:#5a4bf0;--page:#0f0e17;--card:#181725;
--ink:#efeef8;--ink-soft:#aba8c4;--line:#37344c;--line-soft:#28263a;--field:#0f0e17;--error:#ff8f80;--error-bg:#3a1c1a;
--ok:#6fd49b;--ok-bg:#143022;--chip:#28244a;--chip-ink:#c6bfff;--warn:#ffc46b;--warn-bg:#3a2a10;
--lime:#d4ff4f;--lime-ink:#1d2600;--pink:#ffc4de;--pink-ink:#ffc4de;
--shadow:0 18px 40px -18px rgba(0,0,0,.7),0 2px 6px rgba(0,0,0,.4)}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--page);color:var(--ink);
font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
display:flex;flex-direction:column;align-items:center;padding:clamp(0px,6vh,72px) 0 32px}
main{width:100%;max-width:440px;background:var(--card);box-shadow:var(--shadow);overflow:clip}
main.wide{max-width:760px}
@media (min-width:480px){main{border-radius:22px}}
@media (max-width:479px){body{padding:0 0 28px;background:var(--card)}main{box-shadow:none}}
.hero{position:relative;background:var(--brand);color:var(--on-brand);padding:28px 28px 32px}
.theme{position:absolute;top:22px;right:22px;margin:0}
.theme button{display:grid;place-items:center;width:40px;height:40px;padding:0;border-radius:999px;box-shadow:none;
background:color-mix(in srgb,var(--on-brand) 14%,transparent);color:var(--on-brand-soft)}
.theme button:hover,.theme button:focus-visible{background:color-mix(in srgb,var(--on-brand) 26%,transparent);color:var(--on-brand)}
.theme svg{width:19px;height:19px}
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
.tabs a.on{background:var(--chip);color:var(--chip-ink)}
.back{display:inline-flex;align-items:center;gap:6px;margin-top:26px;padding:8px 16px 8px 10px;border-radius:999px;
background:color-mix(in srgb,var(--on-brand) 16%,transparent);color:var(--on-brand);font-weight:700;font-size:.95rem;
text-decoration:none;transition:background .15s,color .15s}
.back svg{width:18px;height:18px;flex:none}
.back:hover,.back:focus-visible{background:var(--lime);color:var(--lime-ink);outline:none}
.back + h1{margin-top:22px}
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
input,select,textarea{width:100%;font:inherit;font-size:1.02rem;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);
background:var(--field);color:var(--ink);transition:border-color .15s}
input:focus,select:focus,textarea:focus{outline:3px solid color-mix(in srgb,var(--brand) 35%,transparent);outline-offset:1px;border-color:var(--brand)}
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
a.button{display:inline-flex;align-items:center;gap:6px;text-decoration:none;border-radius:12px}
a.button svg{width:16px;height:16px;flex:none}
.file-row b.addon-name,.addon-name{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;font-size:1.02rem}
.addon-name .badge{margin-left:0}
.panel{scroll-margin-top:64px}
@media (max-width:540px){.addons .file-row{flex-direction:column;align-items:stretch}.addons .actions.tight{flex-wrap:wrap}}
.state{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
.state p{margin:4px 0 0}
.maker{margin-top:18px}
.maker .item{display:flex;align-items:center;gap:14px}
.maker img{width:56px;height:56px;border-radius:50%;flex:none;background:var(--chip);object-fit:cover}
.maker b{display:block}
.maker .star{display:flex;width:max-content;margin-top:10px}
.star svg{color:var(--warn)}
.maker a{color:inherit}
.links{margin-top:6px}
a.button.quiet{color:var(--ink);border:1.5px solid var(--line);font-weight:650;padding:9px 14px;font-size:.95rem}
a.button.quiet:hover{border-color:var(--ink-soft)}
textarea{resize:vertical;line-height:1.45}
.badge.todo{background:var(--warn-bg);color:var(--warn)}
.actions.tight{margin-top:0;flex-wrap:nowrap}
form.stack{display:grid;gap:18px;margin-top:6px}
form.stack .grid{margin-top:0;gap:18px}
form.stack button.block{margin-top:6px}
form.stack .hint{margin:6px 0 0}
label.check{display:flex;align-items:center;gap:8px;font-weight:500;margin:8px 0 0}
label.check input{width:auto;margin:0}
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
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) summary{color:var(--chip-ink)}}
:root[data-theme=dark] summary{color:var(--chip-ink)}
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
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .drop svg{color:var(--chip-ink)}}
:root[data-theme=dark] .drop svg{color:var(--chip-ink)}
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
<html lang="$lang"$theme_attr><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex,nofollow">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<title>$title</title>
<style>$css</style></head>
<body><main class="$width">
<section class="hero">
$theme
<div class="mark">$icon Selfhost Mail</div>$back
<h1>$headline</h1>
<p>$sub</p>
</section>
$tabs<section class="body">$content</section>
</main>
<footer><a href="$project_url">$project</a> $by $author$source</footer>
</body></html>""")


def page(headline: str, sub: str, content: str, wide: bool = False, tabs: list[tuple[str, str]] | None = None,
         back: tuple[str, str] | None = None, active: str = "") -> str:
    """headline and sub may hold simple markup, so callers escape what they put in. tabs: (anchor, label) links
    to the page's sections ('#anchor'), or to another page ('/settings#apps'), shown under the header and kept in
    view while scrolling; active marks the current one. back: (address, label) for a way back, in the header."""
    def tab(a: str, t: str) -> str:
        href = a if a.startswith("/") else f"#{a}"
        current = ' class="on" aria-current="page"' if active and a.endswith(active) else ""
        return f'<a href="{href}"{current}>{esc(t)}</a>'
    nav = (f'<nav class="tabs" aria-label="{esc(_("Sections"))}">' + "".join(tab(a, t) for a, t in tabs) + "</nav>"
           if tabs else "")
    back_link = (f'<a class="back" href="{esc(back[0])}">{ICON_BACK}<span>{esc(back[1])}</span></a>' if back else "")
    title = re.sub(r"<[^>]+>", "", headline)
    return PAGE.substitute(title=f"{title} · Selfhost Mail", headline=headline, sub=sub, content=content, tabs=nav,
                           css=CSS, icon=ICON_MAIL, width="wide" if wide else "", project=PROJECT,
                           project_url=PROJECT_URL, author=AUTHOR, lang=LANG.get(), by=esc(_("by")), back=back_link,
                           theme=theme_button(), theme_attr=f' data-theme="{THEME.get()}"' if THEME.get() else "",
                           source=(f' · <a href="{esc(SOURCE_URL.get())}">{esc(_("Source code"))}</a>'
                                   if SOURCE_URL.get() else ""))


def panel_css(names: list[str]) -> str:
    """Shows one tab's section at a time: the one in the address (#apps), else the first. The tab of the section
    shown is highlighted. Links to a heading inside a section (#signins) show that section."""
    if not names:
        return ""
    rules = ["@supports selector(:has(a)){.panel{display:none}.panel:target,.panel:has(:target){display:block}",
             ".panels:not(:has(:target))>.panel:first-child{display:block}",
             f'main:not(:has(.panels :target)) .tabs a[href="#{names[0]}"]']
    rules[-1] += ",".join([""] + [f'main:has(#{n}:target,#{n} :target) .tabs a[href="#{n}"]' for n in names])
    rules[-1] += "{background:var(--chip);color:var(--chip-ink)}}"   # without :has (old browsers): all sections show
    return "<style>" + "".join(rules) + "</style>"


def addon_setup(csrf: str, addon: dict, fields: list[dict], flash: tuple[str, str] | None) -> str:
    """One add-on's own page: turn it on or off, and fill in the settings it needs. fields: dicts with full,
    label, help, required, lines, secret, half, value, where ("server", "page" or ""), has_value."""
    name = addon["name"]
    parts = [message(*flash) if flash else ""]
    # on or off, with its button
    if addon["on"]:
        state = f'<span class="badge lime">{esc(_("On"))}</span>'
        note = _("Start a new chat in your AI app to use it.")
    else:
        state = f'<span class="badge">{esc(_("Off"))}</span>'
        note = _("Turn it on to let your AI app use it.")
    if addon.get("missing"):
        state += f' <span class="badge todo">{esc(_("Needs setting up"))}</span>'
    toggle = ""
    if addon.get("library") and not addon.get("in_settings"):
        toggle = _post("/settings/addon", csrf, {"name": name, "action": "off" if addon["on"] else "on", "back": "setup"},
                       _("Turn off") if addon["on"] else _("Turn on"), "quiet" if addon["on"] else "")
    elif addon.get("in_settings") and addon["on"]:
        state += f' <span class="badge">{esc(_("In server settings"))}</span>'
    parts.append(f'<div class="list"><div class="item state"><div><b class="addon-name">{esc(addon_title(name))} {state}</b>'
                 f'<p class="muted">{esc(note)}</p></div>{toggle}</div></div>')
    # the form
    if fields:
        boxes, halves = [], []

        def flush() -> None:
            if halves:
                boxes.append(f'<div class="grid two">{"".join(halves)}</div>')
                halves.clear()

        for f in fields:
            fid = "f_" + f["full"].lower()
            label = esc(_(f["label"])) + ("" if f["required"] else f' <span class="hint">{esc(_("optional"))}</span>')
            hint = f'<p class="hint">{esc(_(f["help"]))}</p>' if f["help"] else ""
            if f["where"] == "server":
                shown = "••••••" if f["secret"] else esc(f["value"])
                box = (f'<div><label>{label}</label><p class="lead"><b>{shown}</b> '
                       f'<span class="badge">{esc(_("In server settings"))}</span></p></div>')
            elif f["lines"] > 1 and not f["secret"]:
                box = (f'<div><label for="{fid}">{label}</label><textarea id="{fid}" name="{esc(f["full"])}" '
                       f'rows="{f["lines"]}">{esc(f["value"])}</textarea>{hint}</div>')
            else:
                kind = "password" if f["secret"] else "text"
                placeholder = esc(_("Saved. Type to replace it.")) if f["secret"] and f["has_value"] else ""
                clear = (f'<label class="check"><input type="checkbox" name="{esc(f["full"])}__clear" value="1"> '
                         f'{esc(_("Remove it"))}</label>' if f["secret"] and f["has_value"] else "")
                box = (f'<div><label for="{fid}">{label}</label><input id="{fid}" type="{kind}" name="{esc(f["full"])}" '
                       f'value="{esc(f["value"])}" placeholder="{placeholder}" autocomplete="off">{hint}{clear}</div>')
            if f.get("half"):
                halves.append(box)
                if len(halves) == 2:
                    flush()
            else:
                flush()
                boxes.append(box)
        flush()
        parts.append(f'<h2>{esc(_("Set up"))}</h2><p class="lead">'
                     + esc(_("Saved on your server, encrypted. Changes count right away.")) + "</p>"
                     f'<form method="post" action="/settings/addon/{esc(name)}" class="stack">{_csrf(csrf)}'
                     f'<input type="hidden" name="name" value="{esc(name)}">{"".join(boxes)}'
                     f'<button class="block" type="submit">{esc(_("Save"))}</button></form>')
    else:
        parts.append(f'<p class="lead" style="margin-top:22px">{esc(_("This add-on needs no settings."))}</p>')
    more = (f'<a href="{LIBRARY_URL}/{esc(name)}">{esc(_("What it does and what to ask your AI app"))}</a>'
            if addon.get("library") and not addon.get("own_file") else "<span></span>")
    parts.append(f'<div class="bar"><span class="muted">{more}</span>'
                 f'<a class="button quiet" href="/settings#addons">{ICON_BACK}{esc(_("All add-ons"))}</a></div>')
    about = _(ADDON_HELP[name]) if name in ADDON_HELP else addon.get("about", "")
    tabs = [("/settings#mailboxes", _("Mailboxes")), ("/settings#apps", _("Apps")), ("/settings#addons", _("Add-ons")),
            ("/settings#about", _("About"))]
    return page(f'<span class="hl">{esc(addon_title(name))}</span>', esc(about), "".join(parts), wide=True,
                tabs=tabs, back=("/settings#addons", _("All add-ons")), active="addons")


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
    return f'<span class="badge {mode}">{esc(_(MODE_LABELS.get(mode, mode)))}</span>'


def mode_options(selected: str) -> str:
    return "".join(f'<option value="{m}"{" selected" if m == selected else ""}>{esc(_(MODE_LABELS[m]))}</option>'
                   for m in MODE_LABELS)


def mode_hint() -> str:
    return '<p class="hint">' + esc(_("Full: read, draft, sort and send. Draft only: everything but sending. "
                                      "Read only: read and search.")) + "</p>"


# ---------------------------------------------------------------- login page (AI apps connecting)

def login(app: str | None, host: str | None, req: str, mailboxes: list[tuple[str, str, str]], error: str = "",
          expired_text: str = "", settings_url: str = "") -> str:
    """mailboxes: (address, mode, name) for every mailbox the server knows."""
    if app is None:
        steps = ('<ol class="steps">' + "".join(f"<li>{esc(s)}</li>" for s in (
            _("Go back to your AI app."), _("Start connecting the mail server again."),
            _("A fresh login page opens. It stays valid for 10 minutes."))) + "</ol>")
        return page(esc(_("This login link has expired")), esc(expired_text or _("Login links last 10 minutes.")), steps)
    a = esc(app)
    if len(mailboxes) > 1:
        boxes = "".join(
            f'<label class="choice"><input type="checkbox" name="mailbox" value="{esc(addr)}" checked>'
            f'<span class="addr">{who(addr, name)}</span>{badge(mode)}</label>' for addr, mode, name in mailboxes)
        choose = (f'<fieldset><legend>{_("Which mailboxes may {app} use?", app=a)}</legend>{boxes}'
                  f'<p class="hint">{esc(_("Each mailbox keeps its own limits: a read-only one stays read-only."))}</p></fieldset>')
    elif mailboxes:
        choose = f'<input type="hidden" name="mailbox" value="{esc(mailboxes[0][0])}">'
    else:
        choose = message("error", _("No mailbox is set up on this server yet. Add one first."))
    if any(mode == "full" for _addr, mode, _name in mailboxes):
        choose += (f'<fieldset><legend>{esc(_("Sending"))}</legend><label class="choice"><input type="checkbox" '
                   f'name="allow_send" value="yes"><span class="addr">{_("Allow {app} to send email", app=a)}</span></label>'
                   '<p class="hint">'
                   + _("<b>Not ticked:</b> {app} writes drafts, and you press send yourself in your mail app.", app=a)
                   + "<br>" + _('<b>Ticked:</b> {app} can also press send for you. Tip: set sending to "ask first" '
                                'in your AI app.', app=a) + "</p></fieldset>")
    local = (host or "").lower() in ("localhost", "127.0.0.1", "::1")
    warn = message("error", _("{app} returns to an app on a computer (localhost). Only continue if that's your own "
                              "computer and you just started this connection there.", app=app)) if local else ""
    content = (f'{message("error", error) if error else ""}{warn}<form method="post" action="/login">'
               f'<input type="hidden" name="req" value="{esc(req)}">{choose}'
               f'<label for="passphrase">{esc(_("Passphrase"))}</label>'
               '<input id="passphrase" type="password" name="passphrase" autocomplete="current-password" autofocus required>'
               f'<button class="block" type="submit">{esc(_("Allow access"))}</button></form>'
               f'<p class="note">{ICON_SHIELD}<span>'
               + esc(_("Only continue if you started this connection yourself, just now. Otherwise close this page: "
                       "nothing happens without your passphrase.")) + "</span></p>"
               + (f'<p class="note">{ICON_CHECK}<span>'
                  + _("Afterwards, manage everything (mailboxes, apps, privacy, files) at <b>{url}</b>, with the same "
                      "passphrase.", url=esc(settings_url)) + "</span></p>" if settings_url else ""))
    return page(_('{app} wants your <span class="hl">mailbox</span>', app=a),
                _("After you allow it, you go back to <b>{host}</b>.", host=esc(host or "?")), content)


# ---------------------------------------------------------------- settings page

ICON_UPLOAD = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
               'stroke-linejoin="round" aria-hidden="true"><path d="M12 15V4"/><path d="m7 9 5-5 5 5"/>'
               '<path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>')


def settings_login(error: str = "", after: str = "/settings") -> str:
    files = after == "/settings/upload"
    content = (f'{message("error", error) if error else ""}<form method="post" action="/settings/login">'
               f'<input type="hidden" name="next" value="{esc(after)}">'
               f'<label for="passphrase">{esc(_("Passphrase"))}</label>'
               '<input id="passphrase" type="password" name="passphrase" autocomplete="current-password" autofocus required>'
               '<label class="confirm remember"><input type="checkbox" name="remember" value="yes" checked>'
               f'{esc(_("Remember this device for 90 days"))}</label>'
               f'<button class="block" type="submit">{esc(_("Open files") if files else _("Open settings"))}</button></form>'
               f'<p class="note">{ICON_SHIELD}<span>'
               + esc(_('Same passphrase as when you connect an AI app. Let your phone or browser save it, so next time '
                       'it fills in by itself. Untick "Remember" on a shared computer. Five wrong tries lock this page '
                       'for 15 minutes.')) + "</span></p>")
    if files:
        return page(esc(_("Files for your emails")), esc(_("Upload a photo or document, then ask your AI app to attach it.")),
                    content)
    return page(esc(_("Settings")), esc(_("Your mailboxes and the AI apps that may use them.")), content)


def _csrf(token: str) -> str:
    return f'<input type="hidden" name="csrf" value="{esc(token)}">'


def _post(action: str, csrf: str, fields: dict[str, str], label: str, cls: str = "quiet", extra: str = "") -> str:
    """label is escaped here."""
    hidden = "".join(f'<input type="hidden" name="{esc(k)}" value="{esc(v)}">' for k, v in fields.items())
    return (f'<form method="post" action="{action}">{_csrf(csrf)}{hidden}{extra}'
            f'<button class="{cls}" type="submit">{esc(label)}</button></form>')


def _host_fields(prefix: str, imap_host: str = "", imap_port: str = "993", smtp_host: str = "", smtp_port: str = "465",
                 username: str = "", smtp_username: str = "") -> str:
    return (f'<div class="grid two">'
            f'<div><label for="{prefix}ih">{esc(_("IMAP server"))}</label><input id="{prefix}ih" name="imap_host" value="{esc(imap_host)}" placeholder="imap.example.com"></div>'
            f'<div><label for="{prefix}ip">{esc(_("IMAP port"))}</label><input id="{prefix}ip" name="imap_port" value="{esc(imap_port)}" inputmode="numeric"></div>'
            f'<div><label for="{prefix}sh">{esc(_("SMTP server"))}</label><input id="{prefix}sh" name="smtp_host" value="{esc(smtp_host)}" placeholder="smtp.example.com"></div>'
            f'<div><label for="{prefix}sp">{esc(_("SMTP port"))}</label><input id="{prefix}sp" name="smtp_port" value="{esc(smtp_port)}" inputmode="numeric"></div>'
            f'<div><label for="{prefix}un">{esc(_("Login name"))} <span class="hint">{esc(_("if not the address"))}</span></label><input id="{prefix}un" name="username" value="{esc(username)}" autocomplete="off"></div>'
            f'<div><label for="{prefix}su">{esc(_("Login name for sending"))} <span class="hint">{esc(_("rarely needed"))}</span></label><input id="{prefix}su" name="smtp_username" value="{esc(smtp_username)}" autocomplete="off"></div>'
            '</div>')


def settings(csrf: str, mailboxes: list[dict], apps: list[dict], flash: tuple[str, str] | None, max_boxes: int,
             server_read_only: bool, about: dict | None = None, uploads_on: bool = False,
             devices: dict | None = None, privacy: list[dict] | None = None, changes: list[dict] | None = None,
             addons: list[dict] | None = None) -> str:
    """mailboxes: dicts with address, mode, source, name, imap_host, imap_port, smtp_host, smtp_port, username,
    smtp_username. apps: dicts with client_id, name, host, grant (list or None)."""
    if flash and flash[0] == "domain":
        icons = {"good": ("ok", ICON_CHECK), "warn": ("tip", ICON_ALERT), "bad": ("error", ICON_ALERT)}
        rows = "".join(f'<p class="msg {icons[level][0]}">{icons[level][1]}<span><b>{esc(name)}</b> {esc(text)}</span></p>'
                       for name, level, text in flash[1]["rows"])
        parts = [f'<h2>{esc(_("Domain check: {domain}", domain=flash[1]["address"].split("@")[1]))}</h2>'
                 f'<p class="lead">{esc(_("What other mail servers see when you send. Green is good."))}</p>{rows}']
    else:
        parts = [message(*flash) if flash else ""]
    if server_read_only:
        parts.append(message("error", _("Read-only mode is on (MAIL_READ_ONLY=on): nothing can be changed or sent, "
                                        "whatever each mailbox's mode says.")))

    # Each tab is its own page: only the section whose tab was picked shows (CSS :target, no scripts).
    shown: list[str] = []

    def panel(name: str) -> None:
        parts.append(("</div>" if shown else '<div class="panels">') + f'<div class="panel" id="{name}">')
        shown.append(name)

    # mailboxes
    panel("mailboxes")
    parts.append(f'<h2>{esc(_("Mailboxes"))}</h2>'
                 f'<p class="lead">{esc(_("The first one is the default. Each mailbox keeps its own mode."))}</p>')
    if mailboxes:
        rows = []
        for i, m in enumerate(mailboxes):
            addr, web = m["address"], m["source"] == "web"
            where = _("Added on this page") if web else _("From the settings file. Change it there.")
            row = [f'<div class="item"><div class="item-head">{who(addr, m["label"]) if m["label"] else f"<b>{esc(addr)}</b>"}'
                   f'{badge(m["mode"])}{"<span class=badge>" + esc(_("Default")) + "</span>" if i == 0 else ""}</div>'
                   f'<div class="muted">{esc(where)} · {esc(_(MODE_HELP[m["mode"]]))}</div><div class="actions">',
                   _post("/settings/mailbox", csrf, {"action": "test", "address": addr}, _("Test login")),
                   _post("/settings/mailbox", csrf, {"action": "domain", "address": addr}, _("Check domain"))]
            row.append("</div>")
            row.append(f'<details><summary>{esc(_("Rename"))}</summary><form method="post" action="/settings/mailbox">{_csrf(csrf)}'
                       f'<input type="hidden" name="action" value="rename"><input type="hidden" name="address" value="{esc(addr)}">'
                       f'<div class="grid"><div><label for="r{i}">{esc(_("Name for this mailbox"))} <span class="hint">'
                       f'{esc(_("like Work or Personal. Leave empty to remove the name"))}</span></label>'
                       f'<input id="r{i}" name="label" value="{esc(m["label"])}" maxlength="40"></div></div>'
                       f'<div class="actions"><button type="submit">{esc(_("Save name"))}</button></div></form></details>')
            if web:
                edit = (f'<details><summary>{esc(_("Edit"))}</summary><form method="post" action="/settings/mailbox">{_csrf(csrf)}'
                        f'<input type="hidden" name="action" value="update"><input type="hidden" name="address" value="{esc(addr)}">'
                        f'<div class="grid two"><div><label for="n{i}">{esc(_("Name on outgoing mail"))}</label><input id="n{i}" name="name" value="{esc(m["name"])}"></div>'
                        f'<div><label for="m{i}">{esc(_("Mode"))}</label><select id="m{i}" name="mode">{mode_options(m["mode"])}</select>{mode_hint()}</div></div>'
                        f'<div class="grid"><div><label for="p{i}">{esc(_("New password"))} <span class="hint">'
                        f'{esc(_("leave empty to keep the current one"))}</span></label>'
                        f'<input id="p{i}" type="password" name="password" autocomplete="new-password"></div></div>'
                        + _host_fields(f"e{i}", m["imap_host"], str(m["imap_port"]), m["smtp_host"], str(m["smtp_port"]),
                                       m["username"], m["smtp_username"])
                        + f'<div class="actions"><button type="submit">{esc(_("Save changes"))}</button></div></form>'
                        + _post("/settings/mailbox", csrf, {"action": "delete", "address": addr}, _("Remove mailbox"), "danger",
                                '<label class="confirm"><input type="checkbox" name="confirm" value="yes" required>'
                                + esc(_("Yes, remove it from this server. Its emails stay in the mailbox.")) + "</label>")
                        + "</details>")
                row.append(edit)
            row.append("</div>")
            rows.append("".join(row))
        parts.append(f'<div class="list">{"".join(rows)}</div>')
    else:
        parts.append(f'<div class="list"><p class="empty">{esc(_("No mailbox yet. Add the first one below."))}</p></div>')

    # add a mailbox
    if len(mailboxes) < max_boxes:
        parts.append(
            f'<h2 id="add">{esc(_("Add a mailbox"))}</h2><p class="lead">'
            + esc(_("For Gmail, iCloud, Yahoo, Fastmail and other known providers the server names fill themselves in. "
                    "Most of them need an app password.")) + "</p>"
            f'<form method="post" action="/settings/mailbox">{_csrf(csrf)}<input type="hidden" name="action" value="add">'
            '<div class="grid two">'
            f'<div><label for="aa">{esc(_("Email address"))}</label><input id="aa" type="email" name="address" required autocomplete="off"></div>'
            f'<div><label for="al">{esc(_("Name for this mailbox"))} <span class="hint">{esc(_("like Work"))}</span></label><input id="al" name="label" maxlength="40" autocomplete="off"></div>'
            f'<div><label for="an">{esc(_("Name on outgoing mail"))}</label><input id="an" name="name" autocomplete="off"></div>'
            f'<div><label for="ap">{esc(_("Password or app password"))}</label><input id="ap" type="password" name="password" required autocomplete="new-password"></div>'
            f'<div><label for="am">{esc(_("Mode"))}</label><select id="am" name="mode">{mode_options("draft")}</select>{mode_hint()}</div>'
            f'</div><details><summary>{esc(_("Server settings"))}</summary><p class="hint">'
            + esc(_("Only needed for providers that aren't filled in by themselves. See docs/email-providers.md."))
            + "</p>" + _host_fields("a") + "</details>"
            f'<div class="actions"><button type="submit">{esc(_("Test and add"))}</button></div></form>')
    else:
        parts.append(f'<p class="lead">{esc(_("This server holds up to {count} mailboxes (MAX_MAILBOXES).", count=max_boxes))}</p>')

    # apps
    panel("apps")
    parts.append(f'<h2>{esc(_("Connected apps"))}</h2>'
                 f'<p class="lead">{esc(_("AI apps that logged in, and the mailboxes each one may use."))}</p>')
    if apps:
        rows = []
        for i, a in enumerate(apps):
            grant = a["grant"]
            ticks = "".join(
                f'<label class="choice"><input type="checkbox" name="mailbox" value="{esc(m["address"])}"'
                f'{" checked" if grant is None or m["address"] in grant else ""}><span class="addr">{who(m["address"], m["label"])}</span>'
                f'{badge(m["mode"])}</label>' for m in mailboxes)
            which = (_("Every mailbox (connected before mailboxes could be chosen)") if grant is None
                     else ", ".join(grant) or _("No mailbox"))
            rows.append(
                f'<div class="item"><div class="item-head"><b>{esc(a["name"])}</b>'
                f'<span class="muted">{esc(_("returns to {host}", host=a["host"]))}</span></div>'
                f'<div class="muted">{esc(which)} · {esc(_("may send") if a["may_send"] else _("may not send"))}</div>'
                f'<details><summary>{esc(_("Choose mailboxes"))}</summary><form method="post" action="/settings/app">{_csrf(csrf)}'
                f'<input type="hidden" name="action" value="grant"><input type="hidden" name="client_id" value="{esc(a["client_id"])}">'
                f'<fieldset style="margin-top:12px">{ticks}</fieldset>'
                f'<label class="choice"><input type="checkbox" name="allow_send" value="yes"{" checked" if a["may_send"] else ""}>'
                f'<span class="addr">{esc(_("May send email"))}</span></label>'
                f'<div class="actions"><button type="submit">{esc(_("Save"))}</button></div></form></details>'
                '<div class="actions">'
                + _post("/settings/app", csrf, {"action": "disconnect", "client_id": a["client_id"]}, _("Disconnect"), "danger")
                + "</div></div>")
        parts.append(f'<div class="list">{"".join(rows)}</div>')
    else:
        parts.append(f'<div class="list"><p class="empty">{esc(_("No app has connected yet."))}</p></div>')

    if uploads_on:
        panel("files")
        parts.append(f'<h2>{esc(_("Files for your emails"))}</h2><p class="lead">'
                     + _('Upload a photo, PDF or document on <a href="/settings/upload">the upload page</a>, then ask '
                         'your AI app to attach it.') + "</p>")

    if privacy is not None:
        panel("privacy")
        parts.append(f'<h2>{esc(_("Privacy"))}</h2><p class="lead">'
                     + esc(_("For files you attach from your computer, the AI or the upload page. Files forwarded from "
                             "other emails are left as they are.")) + "</p>")
        rows = []
        for p in privacy:
            state = (f'<span class="badge lime">{esc(_("On"))}</span>' if p["on"]
                     else f'<span class="badge read">{esc(_("Off"))}</span>')
            if p["forced_off"]:
                button = f'<span class="muted">{esc(_("Off in the server settings"))}</span>'
            else:
                button = _post("/settings/privacy", csrf, {"name": p["name"], "action": "off" if p["on"] else "on"},
                               _("Turn off") if p["on"] else _("Turn on"))
            rows.append(f'<div class="item"><div class="file-row"><div class="grow"><b>{esc(_(p["label"]))} {state}</b>'
                        f'<span class="muted">{esc(_(PRIVACY_HELP.get(p["name"], "")) if PRIVACY_HELP.get(p["name"]) else "")}</span></div>{button}</div></div>')
        rows.append(f'<div class="item"><div class="file-row"><div class="grow"><b>{esc(_("No tracking"))} '
                    f'<span class="badge lime">{esc(_("Always"))}</span></b><span class="muted">'
                    + esc(_("The server never loads pictures or links inside emails, so senders can't see when or where "
                            "you read them.")) + "</span></div></div></div>")
        parts.append(f'<div class="list">{"".join(rows)}</div>')

    if devices is not None:
        panel("devices")
        parts.append(f'<h2>{esc(_("Devices"))}</h2><p class="lead">'
                     + esc(_("Browsers signed in to these pages. Sign out any you don't recognise, then change your "
                             "passphrase.")) + "</p>")
        rows = []
        for d in devices["list"]:
            name = esc(d["device"]) if d["device"] else esc(_("A device"))
            facts = [_("Signed in {when}", when=d["since"]) if d["since"] else "",
                     _("last seen {when}", when=d["seen"]) if d["seen"] and not d["current"] else "",
                     _("from {address}", address=d["ip"]) if d["ip"] else "",
                     _("remembered for 90 days") if d["remember"] else _("until the browser closes")]
            rows.append(
                f'<div class="item"><div class="file-row"><div class="grow"><b>{name}'
                + (f' <span class="badge lime">{esc(_("This device"))}</span>' if d["current"] else "")
                + f'</b><span class="muted">{esc(" · ".join(f for f in facts if f))}</span></div>'
                + _post("/settings/device", csrf, {"action": "signout", "id": d["id"]}, _("Sign out"), "danger")
                + "</div></div>")
        parts.append(f'<div class="list">{"".join(rows)}</div>')
        if devices["on"]:
            parts.append(f'<h2 id="signins">{esc(_("Sign-ins, last 7 days"))}</h2><p class="lead">'
                         + esc(_("Every passphrase try on these pages and on AI app logins. A failed one you didn't make "
                                 "means someone is guessing.")) + "</p>")
            if devices["signins"]:
                events = "".join(
                    f'<div class="item"><div class="item-head"><b>{esc(_("Signed in") if e["ok"] else _("Wrong passphrase"))}</b>'
                    f'<span class="badge{"" if e["ok"] else " fail"}">{esc(e["where"])}</span></div>'
                    f'<div class="muted">{esc(e["time"])} · {esc(e["device"])} · {esc(_("from {address}", address=e["ip"]))}</div></div>'
                    for e in devices["signins"][:50])
                parts.append(f'<div class="list">{events}</div>')
            else:
                parts.append(f'<div class="list"><p class="empty">{esc(_("No sign-ins in the last 7 days."))}</p></div>')
            parts.append('<div class="actions">' + _post("/settings/device", csrf, {"action": "log_off"},
                                                         _("Turn off the device log")) + "</div>"
                         f'<p class="hint">{esc(_("Turning it off deletes this history and stops saving devices and network addresses. Sign-ins keep working."))}</p>')
        elif devices.get("forced_off"):
            parts.append(f'<p class="lead">{_("The device log is off (<code>DEVICE_LOG=off</code> in the server settings).")}</p>')
        else:
            parts.append(f'<p class="lead" style="margin-top:16px">{esc(_("The device log is off: no sign-in history or device details are kept."))}</p>'
                         '<div class="actions">' + _post("/settings/device", csrf, {"action": "log_on"},
                                                         _("Turn on the device log")) + "</div>")

    if changes is not None:
        panel("changes")
        parts.append(f'<h2>{esc(_("Changes by AI apps"))}</h2><p class="lead">'
                     + esc(_("Settings an AI app changed because you asked it to, in the last 30 days. AI apps can only "
                             "change photo location, document details, the update check, your signature, templates and "
                             "uploaded files.")) + "</p>")
        if changes:
            rows = "".join(f'<div class="item"><div class="item-head"><b>{esc(c["what"].splitlines()[0])}</b></div>'
                           f'<div class="muted">{esc(c["time"])} · {esc(c["app"])}</div></div>' for c in changes[:50])
            parts.append(f'<div class="list">{rows}</div>')
        else:
            parts.append(f'<div class="list"><p class="empty">{esc(_("No changes by AI apps."))}</p></div>')

    if addons is not None:
        panel("addons")
        parts.append(f'<h2>{esc(_("Add-ons"))}</h2><p class="lead">'
                     + esc(_("Extra features that come with the server, all off until you turn them on. Each one has a "
                             "page that says what to ask your AI app and which settings it needs.")) + "</p>")
        rows = []
        for a in addons:
            state = (f'<span class="badge lime">{esc(_("On"))}</span>' if a["on"]
                     else f'<span class="badge">{esc(_("Off"))}</span>')
            if not a["library"] or a.get("own_file"):
                state += f' <span class="badge">{esc(_("Your own"))}</span>'
            about_text = _(ADDON_HELP[a["name"]]) if a["name"] in ADDON_HELP else a["about"]
            link = (f'<a href="{LIBRARY_URL}/{esc(a["name"])}">{esc(_("Details"))}</a>'
                    if a["library"] and not a.get("own_file") else "")
            if a["library"] and a.get("in_settings") and a["on"]:
                state += f' <span class="badge">{esc(_("In server settings"))}</span>'
            if a.get("missing"):
                state += f' <span class="badge todo">{esc(_("Needs setting up"))}</span>'
            buttons = []
            if a.get("fields") and re.fullmatch(r"[a-z][a-z0-9_]{0,40}", a["name"]):
                buttons.append(f'<a class="button quiet" href="/settings/addon/{esc(a["name"])}">{esc(_("Set up"))}</a>')
            if a["library"] and not a.get("in_settings"):
                buttons.append(_post("/settings/addon", csrf, {"name": a["name"], "action": "off" if a["on"] else "on"},
                                     _("Turn off") if a["on"] else _("Turn on")))
            button = f'<div class="actions tight">{"".join(buttons)}</div>' if buttons else ""
            rows.append(f'<div class="item"><div class="file-row"><div class="grow"><b class="addon-name">'
                        f'{esc(addon_title(a["name"]))} {state}</b><span class="muted">{esc(about_text)} {link}</span>'
                        f'</div>{button}</div></div>')
        parts.append(f'<div class="list addons">{"".join(rows)}</div>' if rows else
                     f'<div class="list"><p class="empty">{esc(_("No add-ons."))}</p></div>')
        parts.append(f'<p class="hint">{_("Turning one on or off works right away: start a new chat in your AI app to see the change. Add-ons can also be turned on with <code>MAIL_ADDONS</code> in the server settings.")} '
                     f'<a href="{PROJECT_URL}/blob/main/docs/addons.md">{esc(_("How add-ons work"))}</a></p>')

    if about:
        whats_new = esc(_("What's new"))
        upd = about.get("update")
        if upd is None:
            status = ""
        elif upd["newer"]:
            status = (f'<b>{esc(_("Update available: {version}", version=upd["latest"]))}</b>. '
                      f'<a href="{esc(upd["url"])}">{whats_new}</a> · '
                      f'<a href="{PROJECT_URL}/blob/main/docs/updates.md">{esc(_("How to update"))}</a>')
        else:
            status = esc(_("Up to date.")) + (" " + esc(_("Newest release: {version}.", version=upd["latest"]))
                                              if upd["latest"] else "")
        panel("about")
        parts.append(f'<h2>{esc(_("About this server"))}</h2><p class="lead">'
                     f'{_("Version <b>{version}</b>.", version=esc(about["version"]))} {status}</p>')
        on = upd is not None
        upd_badge = (f'<span class="badge lime">{esc(_("On"))}</span>' if on else f'<span class="badge">{esc(_("Off"))}</span>')
        if about.get("update_locked"):
            upd_badge += f' <span class="badge">{esc(_("In server settings"))}</span>'
            button = ""
        else:
            button = _post("/settings/update", csrf, {"action": "off" if on else "on"},
                           _("Turn off") if on else _("Turn on"))
        parts.append(f'<div class="list"><div class="item"><div class="file-row"><div class="grow"><b>'
                     f'{esc(_("Update check"))} {upd_badge}</b><span class="muted">'
                     + esc(_("Once a day the server asks GitHub which version is newest, and tells you here and in your "
                             "AI app. It sends nothing else.")) + f'</span></div>{button}</div></div></div>')
        if about.get("addons") and addons is None:
            parts.append(f'<p class="lead">{_("Add-ons: <b>{names}</b>.", names=esc(", ".join(about["addons"])))}</p>')
        if about.get("changelog"):
            parts.append(f'<details><summary>{whats_new}</summary>'
                         f'<div class="changelog">{about["changelog"]}</div></details>')
        source = SOURCE_URL.get() or PROJECT_URL
        parts.append(f'<p class="hint">{esc(_("Free and open source software under the GNU Affero General Public License v3.0, with no warranty."))} '
                     f'<a href="{esc(source)}">{esc(_("Source code"))}</a> · '
                     f'<a href="https://www.gnu.org/licenses/agpl-3.0.html">{esc(_("License"))}</a></p>')
        profile = f"https://github.com/{AUTHOR}"
        parts.append(f'<div class="list maker"><div class="item"><img src="{profile}.png?size=112" alt="" width="56" '
                     f'height="56" loading="lazy" referrerpolicy="no-referrer"><div><b>'
                     + _("Made by {author}", author=f'<a href="{profile}">{esc(AUTHOR)}</a>') + '</b><span class="muted">'
                     + esc(_("An open-source project. Your mail and passwords never reach the author: they stay on your "
                             "server.")) + "</span>"
                     f'<a class="button quiet star" href="{PROJECT_URL}">{ICON_STAR}{esc(_("Star it on GitHub"))}</a>'
                     "</div></div></div>")
        issues = f"{PROJECT_URL}/issues/new?template="
        links = [(issues + "bug_report.yml", _("Report a problem")),
                 (issues + "question.yml", _("Ask a question or suggest an idea")),
                 (issues + "provider_request.yml", _("My email provider doesn't work")),
                 (issues + "addon.yml", _("Share an add-on")),
                 (f"{PROJECT_URL}/security/advisories/new", _("Report a security problem privately"))]
        parts.append(f'<h2>{esc(_("Help and ideas"))}</h2><div class="actions links">'
                     + "".join(f'<a class="button quiet" href="{esc(u)}">{esc(t)}</a>' for u, t in links) + "</div>"
                     f'<p class="hint">{esc(_("These open GitHub, where reports are public: leave out passwords, email addresses and email content. Security problems go privately to the author."))}</p>')
        parts.append(f'<p class="hint">{esc(_("Page language: {language}. It follows your browser; LANGUAGE in the settings can fix it.", language=LANGUAGES.get(LANG.get(), LANG.get())))}</p>')
    parts.append("</div></div>" if shown else "")
    parts.append(panel_css(shown))
    parts.append(f'<div class="bar"><span class="muted">{esc(_("Changes count right away. Apps never see mail passwords."))}</span>'
                 + _post("/settings/logout", csrf, {}, _("Sign out")) + "</div>")
    tabs = [("mailboxes", _("Mailboxes")), ("apps", _("Apps")), ("files", _("Files")) if uploads_on else None,
            ("privacy", _("Privacy")) if privacy is not None else None,
            ("devices", _("Devices")) if devices is not None else None,
            ("changes", _("AI changes")) if changes is not None else None,
            ("addons", _("Add-ons")) if addons is not None else None,
            ("about", _("About")) if about else None]
    return page('Selfhost Mail <span class="hl">MCP</span>', esc(_("Mailboxes, modes, and which AI apps may use them.")),
                "".join(parts), wide=True, tabs=[t for t in tabs if t])


# ---------------------------------------------------------------- upload page

def _drop(max_size: str, accept: str = "") -> str:
    return (f'<label class="drop">{ICON_UPLOAD}<b>{esc(_("Choose a file"))}</b>'
            f'<span class="muted">{esc(_("Photos, PDFs, documents, audio, video or zip. Up to {size}.", size=max_size))}</span>'
            + (f'<input type="file" name="file" accept="{esc(accept)}" required></label>' if accept
               else '<input type="file" name="file" required></label>')
            + f'<button class="block" type="submit">{esc(_("Upload"))}</button>')


def uploads(csrf: str, files: list[dict], flash: tuple[str, str] | None, max_size: str, accept: str) -> str:
    """files: dicts with code, name, size_text, level, why, used, minutes_left (newest first)."""
    parts = [message(*flash) if flash else ""]
    parts.append(f'<form method="post" action="/settings/upload" enctype="multipart/form-data">{_csrf(csrf)}'
                 + _drop(max_size, accept) + "</form>")
    parts.append(f'<h2 style="margin-top:34px">{esc(_("Waiting to be attached"))}</h2>')
    if files:
        rows = []
        for f in files:
            mins = f["minutes_left"]
            left = _("{count} min", count=mins) if mins < 60 else _("{count} h", count=round(mins / 60))
            status = (_("In a draft · deleted in {time}", time=left) if f["used"]
                      else _("Not used yet · deleted in {time}", time=left))
            warn = (f'<p class="warn">{ICON_ALERT}<span>'
                    + esc(_("Check this: {reason}. Your AI app will ask you before attaching it.", reason=f["why"]))
                    + "</span></p>") if f["level"] == "suspect" else ""
            rows.append(
                f'<div class="item"><div class="file-row">'
                f'<div class="grow"><b>{esc(f["name"])}</b><span class="muted">{esc(f["size_text"])} · {esc(status)} · '
                f'{esc(_("code {code}", code=f["code"]))}</span></div>'
                + _post("/settings/upload", csrf, {"action": "delete", "code": f["code"]}, _("Delete"), "danger")
                + f'</div>{warn}</div>')
        parts.append(f'<div class="list">{"".join(rows)}</div>')
        parts.append('<p class="say">' + _("Then tell your AI app: <q>Attach the file I just uploaded to the email to "
                                           "Sam.</q> Or use its name: <q>Attach {name}.</q>", name=esc(files[0]["name"]))
                     + "</p>")
    else:
        parts.append(f'<div class="list"><p class="empty">{esc(_("Nothing here. Uploaded files show up here with their code."))}</p></div>')
    parts.append(f'<p class="note">{ICON_SHIELD}<span>'
                 + esc(_("Files are stored encrypted. Each one is deleted 1 hour after it first goes into a draft, or "
                         "after 24 hours if it's never used. Your emails keep their own copy. Programs and scripts are "
                         "always refused.")) + "</span></p>")
    parts.append(f'<div class="bar"><a href="/settings">{esc(_("Back to settings"))}</a>'
                 + _post("/settings/logout", csrf, {}, _("Sign out")) + "</div>")
    return page(_('Files for your <span class="hl">emails</span>'), esc(_("Upload a file, then ask your AI app to attach it.")),
                "".join(parts), wide=True)


# ---------------------------------------------------------------- one-time upload link (no passphrase: the link is the key)

def upload_link(error: str = "", done: dict | None = None, max_size: str = "25 MB", expired: bool = False) -> str:
    """done: the stored file's details (name, level, why) after a successful upload."""
    if done:
        warn = (f'<p class="warn">{ICON_ALERT}<span>'
                + esc(_("Check this: {reason}. Your AI app will ask you before attaching it.", reason=done["why"]))
                + "</span></p>") if done.get("level") == "suspect" else ""
        content = (message("ok", _("{name} is uploaded.", name=done["name"])) + warn
                   + f'<p class="lead">{esc(_("Go back to your chat and tell your AI app it is done. This link is now used up."))}</p>')
        return page(_('File <span class="hl">uploaded</span>'), esc(_("It's waiting for your AI app to attach it.")), content)
    if expired:
        steps = ('<ol class="steps">' + "".join(f"<li>{esc(s)}</li>" for s in (
            _("Go back to your chat."), _("Ask your AI app for a new upload link."), _("Open it within 10 minutes.")))
                 + "</ol>")
        return page(esc(_("This link has expired")), esc(error), steps)
    content = (f'{message("error", error) if error else ""}'
               '<form method="post" enctype="multipart/form-data">' + _drop(max_size) + "</form>"
               f'<p class="note">{ICON_SHIELD}<span>'
               + esc(_("Your AI app made this link for one file. It works once and expires 10 minutes after it was "
                       "made. Nothing is sent until you say so in your chat.")) + "</span></p>")
    return page(_('Add a file for your <span class="hl">email</span>'), esc(_("Pick the file, then go back to your chat.")),
                content)
