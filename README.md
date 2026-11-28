# Shade

A private desktop browser on the WebKit engine (GTK4 + WebKitGTK 6), without Chromium.

## Features

- Every tab is a separate identity that lives in memory: its own cookies, its own fingerprint seed, gone when the tab closes
- Tracker and ad blocking (StevenBlack hosts, updated weekly, `~/.cache/shade/hosts.txt`), done by a small C extension (`blokkolo.c`) inside the WebKit web process; it compiles itself on first start
- Cosmetic ad filtering: the `##` rules of EasyList + hufilter (Hungarian sites) with `#@#` exceptions (`~/.cache/shade/`, updated weekly)
- DRM sites (Netflix and similar) do not work: there is no Widevine for WebKitGTK
- Cookie banners hidden (Fanboy Cookie Monster list, `~/.cache/shade/suti.txt`)
- Link target shown at the bottom when you hover a link
- Tracking URL parameters stripped (utm_*, fbclid, gclid…), http upgraded to https with fallback
- Third-party cookies blocked, Intelligent Tracking Prevention (ITP), `Sec-GPC: 1` on every request
- Canvas, audio and WebGL fingerprints randomized per identity
- DNS: the system resolver (WebKitGTK has no DoH), so local `*.park.lan` names work; in Tor mode name resolution also goes through Tor and `.onion` addresses open
- WebRTC: the local address is only visible after a camera/microphone permission; fully off in Tor mode
- Tor mode: starts its own tor process (port 9350) if none is running; time zone UTC; verified: check.torproject.org → IsTor true
- Shield menu: blocked domains, disable blocking on this site, JavaScript on/off per identity, clear cookies
- Reader mode (Ctrl Shift R); tab menu (right click): mute, duplicate, reopen in a new identity, close others
- Encrypted bookmarks: scrypt key from a password, AES-GCM, `~/.local/share/shade/konyvjelzok.bin` (0600); nothing can be read from the file without the password
- Address bar completion from bookmarks and open tabs
- Sleeping tabs: the web process of a silent tab that has been in the background for 10 minutes stops, and the tab reloads when you click it
- Keyword search in the address bar: `w` (Hungarian Wikipedia), `wen`, `yt`, `gh`, `osm`, `arch`, `aur`, `mdn`, `pypi`, `sp` (Startpage), `ddg`, for example `w Siege of Budapest`
- Security level in the shield menu (like Tor Browser): Normal, Safer (WebGL off, JavaScript off on plain http), Safest (JavaScript and WebGL off everywhere)
- Force dark mode on every site (shield menu or Ctrl K)
- Read aloud: set the Piper binary and voice with `SHADE_PIPER` and `SHADE_HANG`; nothing leaves the computer
- Downloads button on the toolbar (this session's downloads, open, show folder)
- Video, PDF, full screen, downloads, camera/microphone with permission prompts, screen sharing, developer tools

## Install

```sh
git clone https://github.com/Botirocky/shade && cd shade && ./telepit.sh
```

It installs the missing packages (on Arch with pacman: webkitgtk-6.0, gtk4, python-gobject, gcc, python-cryptography, tor, alsa-utils), and creates the `shade` command, the icon and the menu entry (with a Tor mode launcher). Uninstall: `./telepit.sh --eltavolit`. Default browser: `xdg-settings set default-web-browser shade.desktop`.

## Start

    python shade.py [url…] [--tor]

Set the search engine with the `SHADE_KERESO` environment variable.

## Keys

| | |
|---|---|
| Ctrl T | new tab with a new identity |
| Ctrl Shift N | new tab in the same identity |
| Ctrl Shift T | reopen closed tab |
| Ctrl D | bookmark on/off (star in the address bar) |
| Ctrl K | command palette: tabs, bookmarks and commands in one place |
| Ctrl \\ | split view on/off (two tabs side by side; tab menu: "Open in split view") |
| Ctrl U | page source |
| Ctrl Shift C | copy link |
| Ctrl Shift S | screenshot of the visible area |
| Ctrl + / − / 0 | zoom, remembered per site (in memory only) |
| Ctrl 1–8 / Ctrl 9 | go to tab n / the last tab |
| Ctrl W / middle click | close tab |
| Ctrl Shift Del | wipe: all tabs, identities, closed tabs, zoom levels and the clipboard; locks the bookmarks |
| Ctrl Shift O | Tor mode on/off (restarts) |
| Ctrl Shift R | reader mode |
| Ctrl M | mute |
| Ctrl F | find in page with match count (Enter / Shift+Enter: next / previous, Esc: close) |
| Ctrl Shift U | read aloud with a local Piper voice (selection or the article text); again: stop |
| Ctrl Shift L | in Tor mode: new Tor circuit and reopen the page in a new identity |
| Ctrl L, Ctrl P, F12 | address, PDF, developer tools |

Test: `python szuro.py`

The user interface is in Hungarian.
