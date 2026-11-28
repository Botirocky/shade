import html
import json
import math
import os
import random
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import konyvjelzo
import szuro

MAPPA = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "shade"
ADAT = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "shade"
for _uj in (CACHE, ADAT):
    if not _uj.exists() and _uj.with_name("arnyek").is_dir():
        _uj.with_name("arnyek").rename(_uj)
CACHE.mkdir(parents=True, exist_ok=True)
HOSTS_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
EASYLIST_URL = "https://easylist.to/easylist/easylist.txt"
HUFILTER_URL = "https://raw.githubusercontent.com/hufilter/hufilter/gh-pages/hufilter.txt"
SUTI_URL = "https://secure.fanboy.co.nz/fanboy-cookiemonster.txt"
KERESO = os.environ.get("SHADE_KERESO", "https://duckduckgo.com/?q={}")
ARGS = sys.argv[1:]
TOR = "--tor" in ARGS
PIPER = os.environ.get("SHADE_PIPER", str(Path.home() / "Dokumentumok/projectek/hang-asszisztens/.venv/bin/piper"))
PIPER_HANG = os.environ.get("SHADE_HANG", str(Path.home() / "Dokumentumok/projectek/hang-asszisztens/hangok/hu_HU-anna-medium.onnx"))
SZINTEK = ["Normál", "Szigorúbb", "Legszigorúbb"]
TILTOTT_F = CACHE / "tiltott.txt"
ENGEDETT_F = CACHE / "engedett.txt"
ENGEDETT: set[str] = set()
if TOR:
    os.environ["TZ"] = "UTC"
    time.tzset()

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gdk, Gio, GLib, Graphene, Gtk, Pango, WebKit

SZIN = {
    "mely": "#0f0f10", "hatter": "#141415", "felulet": "#19191b", "emelt": "#232325", "vonal": "rgba(237,237,237,0.08)",
    "szoveg": "#ededed", "masod": "#a1a1a6", "halk": "#85858b", "lampa": "#d0583f", "kijeloles": "#a9452f",
}
IDENTITAS_SZINEK = ["#c9a15b", "#8fa98a", "#7f97b8", "#c07a5f", "#a68bb0", "#6fa6a0"]

IKON = {
    "vissza": '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
    "elore": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "frissit": '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>',
    "plusz": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "pajzs": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "lakat": '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "nyitott": '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/>',
    "halo": '<rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><path d="M12 12V8"/>',
    "csillag": '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>',
    "letoltes": '<path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>',
    "kereso": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "fel": '<path d="m18 15-6-6-6 6"/>',
    "le": '<path d="m6 9 6 6 6-6"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "radir": '<path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/><path d="M22 21H7"/><path d="m5 11 9 9"/>',
}

SOTET_CSS = ("html{filter:invert(.92) hue-rotate(180deg)!important;background:#fff!important}"
             "img,video,picture,canvas,iframe,embed,object,svg image,[style*='background-image']{filter:invert(1) hue-rotate(180deg)!important}")


def ujjlenyomat_svg(mag: str, szin: str) -> str:
    r = random.Random(int(mag, 16))
    fazis = [r.uniform(0, math.tau) for _ in range(4)]
    torzit = r.uniform(0.10, 0.22)
    utak, minden = [], []
    n = 24
    for i in range(n):
        sugar = 10 + i * 6.4
        res = r.uniform(0.18, 0.42) * (i / n) if i > 13 else 0
        torespont = r.uniform(0, math.tau)
        pontok = []
        for k in range(161):
            t = math.tau * k / 160
            szog = (t - math.pi / 2) % math.tau
            if res and min(abs(szog), math.tau - abs(szog)) < res * math.pi:
                pontok.append(None)
                continue
            if abs(((t - torespont + math.pi) % math.tau) - math.pi) < 0.05 + 0.02 * (i % 3):
                pontok.append(None)
                continue
            rr = sugar * (1 + torzit * (i / n) * math.sin(t + fazis[0]) + 0.05 * math.sin(2 * t + fazis[1]) + 0.025 * math.sin(3 * t + fazis[2]))
            pontok.append((160 + rr * math.cos(t) * 0.86, 176 - i * 1.6 + rr * math.sin(t) * 1.08))
        minden += [p for p in pontok if p]
        d, rajzol = [], False
        for p in pontok:
            if p is None:
                rajzol = False
                continue
            d.append(f"{'L' if rajzol else 'M'}{p[0]:.1f} {p[1]:.1f}")
            rajzol = True
        atl = 0.92 - 0.6 * i / n
        utak.append(f'<path d="{"".join(d)}" stroke-opacity="{atl:.2f}"/>')
    x0, x1 = min(p[0] for p in minden) - 8, max(p[0] for p in minden) + 8
    y0, y1 = min(p[1] for p in minden) - 8, max(p[1] for p in minden) + 8
    return (f'<svg viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{szin}" '
            f'stroke-width="1.6" stroke-linecap="round" aria-label="Az identitás zajosított ujjlenyomata">{"".join(utak)}</svg>')


def css_js(css: str) -> str:
    return f"{{const s=new CSSStyleSheet();s.replaceSync({json.dumps(css)});document.adoptedStyleSheets=[...document.adoptedStyleSheets,s]}}"


def port_nyitva(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


TOR_PORT = 9050 if (TOR and port_nyitva(9050)) else 9350


def gazda(uri: str | None) -> str:
    return (urlsplit(uri or "").hostname or "") if uri else ""


def ures(uri: str | None) -> bool:
    return uri in (None, "", "about:blank")


def kiterjesztes() -> Path | None:
    forras = MAPPA / "blokkolo.c"
    mappa = CACHE / "kiterjesztes"
    so = mappa / "libshade-blokkolo.so"
    if so.exists() and so.stat().st_mtime >= forras.stat().st_mtime:
        return mappa
    try:
        mappa.mkdir(parents=True, exist_ok=True)
        jelzok = subprocess.run(["pkg-config", "--cflags", "--libs", "webkitgtk-web-process-extension-6.0"],
                                capture_output=True, text=True, check=True).stdout.split()
        subprocess.run(["cc", "-shared", "-fPIC", "-O2", "-o", str(so), str(forras), *jelzok], check=True)
        return mappa
    except (OSError, subprocess.CalledProcessError) as h:
        print(f"shade: a blokkoló nem fordult le, követők nem lesznek blokkolva ({h})", file=sys.stderr)
        return None


_ikonok: dict = {}


def textura(nev: str, szin: str = SZIN["masod"], kitolt: bool = False) -> Gdk.Texture:
    k = (nev, szin, kitolt)
    if k not in _ikonok:
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="{szin if kitolt else "none"}" '
               f'stroke="{szin}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{IKON[nev]}</svg>')
        _ikonok[k] = Gdk.Texture.new_from_bytes(GLib.Bytes.new(svg.encode()))
    return _ikonok[k]


def kep(nev: str, szin: str = SZIN["masod"]) -> Gtk.Image:
    i = Gtk.Image.new_from_paintable(textura(nev, szin))
    i.set_pixel_size(16)
    return i


def gomb(nev: str, fv, tipp: str = "") -> Gtk.Button:
    b = Gtk.Button(child=kep(nev), tooltip_text=tipp or None)
    b.add_css_class("ikongomb")
    b.connect("clicked", lambda _: fv())
    return b


def szoveg_gomb(nev: str, szoveg: str, fv) -> Gtk.Button:
    h = Gtk.Box(spacing=10)
    h.append(kep(nev))
    c = Gtk.Label(label=szoveg, xalign=0)
    h.append(c)
    b = Gtk.Button(child=h)
    b.add_css_class("oldalgomb")
    b.cimke = c
    b.connect("clicked", lambda _: fv())
    return b


def cimke(szoveg: str, osztaly: str = "cimke", **kw) -> Gtk.Label:
    c = Gtk.Label(label=szoveg, **{"xalign": 0, **kw})
    c.add_css_class(osztaly)
    return c


class Blokklista(threading.Thread):
    def __init__(self, kesz):
        super().__init__(daemon=True)
        self.kesz = kesz
        self.lista = set(szuro.ALAP_TILTOTT)
        self.css = ""
        self.oldal: dict[str, list[str]] = {}
        self.kivetel: dict[str, set[str]] = {}

    def run(self):
        try:
            adat = self.friss("hosts.txt", HOSTS_URL, lambda a: len(szuro.hosts_beolvas(a)) > 1000)
            if adat:
                self.lista = set(szuro.ALAP_TILTOTT) | szuro.hosts_beolvas(adat)
            adat = self.friss("easylist.txt", EASYLIST_URL, lambda a: a.count("##") > 1000)
            hu = self.friss("hufilter.txt", HUFILTER_URL, lambda a: a.count("##") > 100)
            suti = self.friss("suti.txt", SUTI_URL, lambda a: a.count("##") > 1000)
            self.lista = self.lista | szuro.abp_tartomanyok(hu)
            if adat or hu or suti:
                altalanos, self.oldal, self.kivetel = szuro.kozmetikus_beolvas(adat + "\n" + hu + "\n" + suti)
                self.css = szuro.kozmetikus_css(altalanos)
        except Exception as h:
            print(f"shade: tiltólista hiba: {h}", file=sys.stderr)
        TILTOTT_F.write_text("\n".join(sorted(self.lista)) + "\n")
        GLib.idle_add(self.kesz)

    def friss(self, nev, url, jo) -> str:
        f = CACHE / nev
        if not TOR and (not f.exists() or time.time() - f.stat().st_mtime > 7 * 86400):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "shade"})
                adat = urllib.request.urlopen(req, timeout=20).read().decode(errors="ignore")
                if jo(adat):
                    f.write_text(adat)
            except OSError:
                pass
        return f.read_text(errors="ignore") if f.exists() else ""


class TorIndito(threading.Thread):
    def __init__(self, jelez):
        super().__init__(daemon=True)
        self.jelez = jelez
        self.folyamat = None

    def allapot(self, n):
        GLib.idle_add(self.jelez, n)

    def run(self):
        if port_nyitva(TOR_PORT):
            self.allapot(100)
            return
        adat = CACHE / "tor"
        adat.mkdir(parents=True, exist_ok=True, mode=0o700)
        torrc = CACHE / "torrc"
        torrc.touch()
        try:
            self.folyamat = subprocess.Popen(
                ["tor", "--defaults-torrc", str(torrc), "-f", str(torrc), "--SocksPort", str(TOR_PORT), "--DataDirectory", str(adat),
                 "--ControlPort", f"127.0.0.1:{TOR_PORT + 1}", "--CookieAuthentication", "1", "--Log", "notice stdout"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
        except FileNotFoundError:
            self.allapot(-1)
            return
        utolso = 0
        for sor in self.folyamat.stdout:
            m = re.search(r"Bootstrapped (\d+)%", sor)
            if m:
                utolso = int(m.group(1))
                self.allapot(utolso)
        if utolso < 100:
            self.allapot(-2)


class Identitas:
    szamlalo = 0

    def __init__(self, ablak):
        Identitas.szamlalo += 1
        self.szin = IDENTITAS_SZINEK[(Identitas.szamlalo - 1) % len(IDENTITAS_SZINEK)]
        self.mag = secrets.token_hex(4)
        self.nev = self.mag[:4].upper()
        self.kivetelek: set[str] = set()
        self.lapok = 0
        self.js = True
        self.munkamenet = WebKit.NetworkSession.new_ephemeral()
        m = self.munkamenet
        m.set_itp_enabled(True)
        m.get_cookie_manager().set_accept_policy(WebKit.CookieAcceptPolicy.NO_THIRD_PARTY)
        if TOR:
            m.set_proxy_settings(WebKit.NetworkProxyMode.CUSTOM, WebKit.NetworkProxySettings.new(f"socks5://127.0.0.1:{TOR_PORT}", None))
        m.connect("download-started", ablak.letoltes)
        self.tartalom = WebKit.UserContentManager()
        self.tartalom.add_script(WebKit.UserScript.new(
            (MAPPA / "ujjlenyomat.js").read_text().replace("__MAG__", self.mag),
            WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserScriptInjectionTime.START, None, None))
        self.kozmetika(ablak)

    def kozmetika(self, ablak):
        t = self.tartalom
        t.remove_all_style_sheets()
        if ablak.blokk.css:
            t.add_style_sheet(WebKit.UserStyleSheet.new(
                ablak.blokk.css, WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserStyleLevel.USER,
                None, [f"*://{h}/*" for h in sorted(ENGEDETT)] or None))
        if ablak.sotet:
            t.add_style_sheet(WebKit.UserStyleSheet.new(
                SOTET_CSS, WebKit.UserContentInjectedFrames.TOP_FRAME, WebKit.UserStyleLevel.USER, None, None))


def engedely_nev(k) -> str | None:
    if isinstance(k, WebKit.UserMediaPermissionRequest):
        if WebKit.user_media_permission_is_for_display_device(k):
            return "képernyőmegosztás"
        a, v = k.props.is_for_audio_device, k.props.is_for_video_device
        return "kamera és mikrofon" if a and v else "kamera" if v else "mikrofon"
    for osztaly, nev in [
        ("GeolocationPermissionRequest", "pontos helyzet"), ("NotificationPermissionRequest", "értesítések"),
        ("ClipboardPermissionRequest", "vágólap"), ("PointerLockPermissionRequest", "egérzár"),
        ("WebsiteDataAccessPermissionRequest", "sütik elérése beágyazott oldalként"),
    ]:
        if isinstance(k, getattr(WebKit, osztaly, ())):
            return nev
    return None


class Lap(WebKit.WebView):
    def __init__(self, ablak, identitas, rokon=None):
        if rokon:
            super().__init__(related_view=rokon, user_content_manager=identitas.tartalom)
        else:
            super().__init__(network_session=identitas.munkamenet, user_content_manager=identitas.tartalom)
        self.ablak = ablak
        self.identitas = identitas
        identitas.lapok += 1
        self.blokkolva = Counter()
        self.felhuzott: set[str] = set()
        self.host = ""
        self.utoljara = time.monotonic()
        self.alszik = False
        self.set_hexpand(True)
        self.set_vexpand(True)
        s = WebKit.Settings(
            enable_developer_extras=True, enable_dns_prefetching=False, enable_hyperlink_auditing=False,
            javascript_can_open_windows_automatically=False, media_playback_requires_user_gesture=True,
            enable_webrtc=not TOR, enable_media_stream=True, enable_encrypted_media=False,
            allow_file_access_from_file_urls=False, allow_universal_access_from_file_urls=False,
            enable_page_cache=True,
        )
        self.set_settings(s)
        self.connect("decide-policy", self.dontes)
        self.connect("create", self.uj_ablak)
        self.connect("load-changed", self.betoltes)
        self.connect("load-failed", self.hiba)
        self.connect("permission-request", self.engedely)
        self.connect("enter-fullscreen", lambda _: ablak.teljes_kepernyo(True) or False)
        self.connect("leave-fullscreen", lambda _: ablak.teljes_kepernyo(False) or False)
        self.connect("show-notification", self.ertesites)
        self.connect("user-message-received", self.uzenet)
        self.connect("mouse-target-changed", lambda _, t, __: ablak.link_mutat(self, t.get_link_uri() if t.context_is_link() else ""))
        for p in ("uri", "title", "is-playing-audio", "is-muted"):
            self.connect(f"notify::{p}", lambda *_: ablak.lap_frissult(self))
        self.connect("notify::estimated-load-progress", lambda *_: ablak.tolto_frissit(self))
        fc = self.get_find_controller()
        fc.connect("counted-matches", lambda _, n: ablak.talalat_jelez(self, n))
        fc.connect("failed-to-find-text", lambda _: ablak.talalat_jelez(self, 0))

    def dontes(self, _, d, tipus):
        if tipus == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            s = d.get_navigation_action().get_request().get_uri()
            uj = szuro.tisztit(s) or szuro.https_ra(s, self.identitas.kivetelek)
            if uj:
                if uj.startswith("https://") and s.startswith("http://"):
                    self.felhuzott.add(gazda(s))
                d.ignore()
                self.load_uri(uj)
                return True
            szint = self.ablak.szint
            js = self.identitas.js and not (szint == 2 or (szint == 1 and s.startswith("http://") and not szuro.helyi(gazda(s))))
            st = self.get_settings()
            st.set_enable_javascript(js)
            st.set_enable_webgl(szint == 0)
        elif tipus == WebKit.PolicyDecisionType.RESPONSE and not d.is_mime_type_supported():
            d.download()
            return True
        return False

    def uj_ablak(self, _, akcio):
        hatter = akcio.get_mouse_button() == 2 or bool(akcio.get_modifiers() & Gdk.ModifierType.CONTROL_MASK)
        return self.ablak.uj_lap(self.identitas, hatterben=hatter, rokon=self)

    def betoltes(self, _, esemeny):
        u = self.get_uri() or ""
        if esemeny == WebKit.LoadEvent.COMMITTED:
            h = gazda(u)
            if h != self.host:
                self.host = h
                self.blokkolva.clear()
                self.set_zoom_level(self.ablak.nagyitas.get(h, 1.0))
        elif esemeny == WebKit.LoadEvent.FINISHED:
            h = gazda(u)
            sel = szuro.oldal_szelektorok(h, self.ablak.blokk.oldal, self.ablak.blokk.kivetel) if h and h not in ENGEDETT else []
            if sel:
                self.evaluate_javascript(css_js(szuro.kozmetikus_css(sel)), -1, "shade", None, None, None)
        self.ablak.lap_frissult(self)

    def hiba(self, _, esemeny, uri, h):
        host = gazda(uri)
        if uri.startswith("https://") and host in self.felhuzott and host not in self.identitas.kivetelek \
                and not h.matches(WebKit.NetworkError.quark(), WebKit.NetworkError.CANCELLED):
            self.identitas.kivetelek.add(host)
            self.load_uri("http://" + uri[len("https://"):])
            return True
        return False

    def blokk(self, d):
        self.blokkolva[d] += 1
        self.ablak.munkamenet[d] += 1
        self.ablak.lap_frissult(self)

    def uzenet(self, _, u):
        if u.get_name() == "blokk":
            self.blokk(u.get_parameters().get_string())
            return True
        return False

    def engedely(self, _, k):
        nev = engedely_nev(k)
        if not nev:
            k.deny()
            return True
        self.ablak.kerdes("Engedély", f"{self.host or 'Az oldal'} ehhez kér hozzáférést: {nev}\n\nCsak erre az identitásra és csak most.",
                          lambda igen: k.allow() if igen else k.deny())
        return True

    def ertesites(self, _, n):
        subprocess.Popen(["notify-send", "-a", "Shade", "--", n.get_title() or "Shade", n.get_body() or ""])
        return True

    def uj_lap_oldal(self):
        self.load_html(self.ablak.kezdolap(self.identitas), None)


class Pont(Gtk.DrawingArea):
    def __init__(self, szin):
        super().__init__(content_width=8, content_height=8, valign=Gtk.Align.CENTER)
        rgba = Gdk.RGBA()
        rgba.parse(szin)
        self.set_draw_func(lambda _, cr, w, h: (cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, 1), cr.arc(w / 2, h / 2, 4, 0, math.tau), cr.fill()))


class LapSor(Gtk.ListBoxRow):
    def __init__(self, szin):
        super().__init__()
        h = Gtk.Box(spacing=10)
        h.append(Pont(szin))
        self.cim = cimke("Új lap", "lapcim", hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        self.szam = cimke("", "szam")
        h.append(self.cim)
        h.append(self.szam)
        self.set_child(h)

    def beallit(self, cim, szam, hang=""):
        self.cim.set_label(cim or "Új lap")
        self.szam.set_label(" ".join(x for x in (hang, str(szam) if szam else "") if x))


def stilus() -> str:
    S = SZIN
    return f"""
* {{ font-family: Inter, sans-serif; font-size: 13px; color: {S['szoveg']}; }}
window, .jobb {{ background: {S['hatter']}; }}
.oldalsav {{ background: {S['mely']}; border-right: 1px solid {S['vonal']}; padding: 0 12px 12px 12px; }}
.marka {{ font-size: 15px; font-weight: 500; }}
.mod, .szam, .allapotertek {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {S['halk']}; }}
.cimke {{ font-size: 12px; color: {S['halk']}; padding: 0 8px; }}
.allapotnev {{ color: {S['masod']}; }}
.lapcim {{ color: {S['masod']}; }}
.linkcimke {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {S['masod']}; background: {S['felulet']}; border: 1px solid {S['vonal']}; border-radius: 0 6px 0 0; padding: 3px 8px; }}
list, listview {{ background: transparent; }}
list row {{ min-height: 36px; margin-bottom: 2px; border-radius: 8px; border: 1px solid transparent; padding: 0 8px; }}
list row:selected {{ background: {S['emelt']}; border-color: {S['vonal']}; }}
list row:hover:not(:selected) {{ background: {S['felulet']}; }}
.eszkozsor {{ background: {S['hatter']}; border-bottom: 1px solid {S['vonal']}; padding: 0 12px; }}
entry {{ background: {S['felulet']}; border: 1px solid {S['vonal']}; border-radius: 8px; min-height: 30px; padding: 0 8px; box-shadow: none; outline: none; }}
entry:focus-within {{ background: {S['emelt']}; border-color: rgba(237,237,237,0.20); }}
entry selection {{ background: {S['kijeloles']}; color: #fff; }}
button {{ background: transparent; border: 1px solid transparent; border-radius: 8px; box-shadow: none; min-height: 30px; padding: 0 8px; }}
button:hover {{ background: {S['emelt']}; }}
button:active {{ background: {S['felulet']}; }}
button:focus-visible {{ outline: 1px solid rgba(237,237,237,0.20); }}
button label {{ font-weight: normal; }}
.ikongomb {{ min-width: 30px; padding: 0; }}
.oldalgomb {{ color: {S['masod']}; }}
.oldalgomb:hover {{ background: {S['felulet']}; }}
.oldalgomb label {{ color: {S['masod']}; }}
.pajzs label {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {S['masod']}; }}
popover > contents {{ background: {S['emelt']}; border: 1px solid {S['vonal']}; border-radius: 12px; padding: 4px; box-shadow: 0 8px 24px rgba(0,0,0,.4); }}
popover button {{ padding: 6px 12px; }}
popover button:hover {{ background: rgba(237,237,237,0.06); }}
popover .info {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {S['halk']}; padding: 6px 12px; }}
popover separator {{ background: {S['vonal']}; margin: 4px 8px; min-height: 1px; }}
popover checkbutton {{ padding: 6px 8px; border-radius: 8px; }}
popover checkbutton:hover {{ background: rgba(237,237,237,0.06); }}
checkbutton check {{ background: {S['felulet']}; border: 1px solid rgba(237,237,237,0.2); border-radius: 4px; min-width: 14px; min-height: 14px; }}
checkbutton check:checked {{ background: {S['lampa']}; border-color: {S['lampa']}; }}
.parancssor {{ background: {S['emelt']}; border: 1px solid {S['vonal']}; border-radius: 12px; padding: 8px; }}
.parancssor entry {{ min-height: 38px; font-size: 14px; }}
.kieg row {{ min-height: 28px; }}
.kieg label {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: {S['masod']}; }}
paned > separator {{ background: {S['vonal']}; min-width: 1px; }}
.csik {{ min-height: 2px; background: transparent; }}
.csik.aktiv {{ background: {S['lampa']}; }}
progressbar trough {{ background: transparent; min-height: 2px; border: none; }}
progressbar progress {{ background: {S['lampa']}; min-height: 2px; border-radius: 0; }}
tooltip {{ background: {S['emelt']}; border: 1px solid {S['vonal']}; border-radius: 6px; }}
scrollbar slider {{ background: {S['emelt']}; min-width: 6px; border-radius: 4px; }}
.parbeszed {{ background: {S['felulet']}; padding: 20px; }}
"""


class Ablak(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Shade", default_width=1360, default_height=860)
        self.munkamenet = Counter()
        self.blokk = Blokklista(self.blokk_kesz)
        self.bezartak: list[tuple[str, Identitas]] = []
        self.nagyitas: dict[str, float] = {}
        self.szint = 0
        self.sotet = False
        self.felolvaso: list[subprocess.Popen] = []
        self.lapok: list[Lap] = []
        self.letoltesek: list[dict] = []
        self.osztott: Lap | None = None
        self.osztott_fokusz = False
        self.csendes = False
        self.szef = konyvjelzo.Szef(ADAT / "konyvjelzok.bin")

        fo = Gtk.Box()
        self.set_child(fo)
        self.oldalsav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request=256)
        self.oldalsav.add_css_class("oldalsav")
        fo.append(self.oldalsav)
        ov = self.oldalsav
        fej = Gtk.Box(height_request=48, margin_start=8, margin_end=8)
        fej.append(cimke("Shade", "marka", hexpand=True))
        self.mod = cimke("", "mod")
        fej.append(self.mod)
        ov.append(fej)
        ov.append(cimke("Lapok", margin_top=12, margin_bottom=4))
        self.lista = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.lista.connect("row-selected", lambda _, r: None if self.csendes or r is None else self.valt(r.get_index()))
        katt = Gtk.GestureClick(button=0)
        katt.connect("pressed", self.lista_katt)
        self.lista.add_controller(katt)
        ov.append(Gtk.ScrolledWindow(child=self.lista, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER))
        ov.append(cimke("Könyvjelzők", margin_top=16, margin_bottom=4))
        self.kj_lista = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, activate_on_single_click=True)
        self.kj_lista.connect("row-activated", lambda _, r: self.akt().load_uri(r.url))
        kk = Gtk.GestureClick(button=3)
        kk.connect("pressed", self.kj_menu)
        self.kj_lista.add_controller(kk)
        self.kj_gorgo = Gtk.ScrolledWindow(child=self.kj_lista, max_content_height=5 * 38, propagate_natural_height=True,
                                           hscrollbar_policy=Gtk.PolicyType.NEVER)
        ov.append(self.kj_gorgo)
        self.kj_nyit = szoveg_gomb("lakat", "Feloldás", lambda: self.kj_felold(self.kj_frissit))
        ov.append(self.kj_nyit)
        ov.append(cimke("Állapot", margin_top=16, margin_bottom=4))
        racs = Gtk.Grid(column_spacing=12, row_spacing=4, margin_start=8, margin_end=8)
        self.allapot: dict[str, Gtk.Label] = {}
        for i, nev in enumerate(["Tiltólista", "DNS", "Szint", "Identitás", "Letöltés"]):
            c = cimke(nev, "allapotnev", hexpand=True)
            e = cimke("", "allapotertek", xalign=1)
            racs.attach(c, 0, i, 1, 1)
            racs.attach(e, 1, i, 1, 1)
            self.allapot[nev] = e
            if nev == "Letöltés":
                self.letoltes_sor = (c, e)
                c.set_visible(False)
                e.set_visible(False)
        ov.append(racs)
        ov.append(Gtk.Box(height_request=16))
        ov.append(szoveg_gomb("plusz", "Új identitás", lambda: self.uj_lap()))
        ov.append(szoveg_gomb("radir", "Kiürítés", self.kiurit))
        ov.append(szoveg_gomb("halo", "Kilépés a Torból" if TOR else "Tor mód", self.tor_valt))

        jobb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        jobb.add_css_class("jobb")
        fo.append(jobb)
        self.eszkozsor = Gtk.Box(height_request=48, spacing=4)
        self.eszkozsor.add_css_class("eszkozsor")
        eh = self.eszkozsor
        for nev, fv in [("vissza", lambda: self.akt().go_back()), ("elore", lambda: self.akt().go_forward()), ("frissit", lambda: self.akt().reload())]:
            b = gomb(nev, fv)
            b.set_valign(Gtk.Align.CENTER)
            eh.append(b)
        self.cim = Gtk.Entry(hexpand=True, valign=Gtk.Align.CENTER, placeholder_text="Keresés vagy cím", margin_start=8, margin_end=8)
        self.cim.set_icon_from_paintable(Gtk.EntryIconPosition.PRIMARY, textura("lakat"))
        self.cim.set_icon_from_paintable(Gtk.EntryIconPosition.SECONDARY, textura("csillag"))
        self.cim.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, "Könyvjelző (Ctrl+D)")
        self.cim.connect("icon-press", lambda _, p: self.kj_hozzaad() if p == Gtk.EntryIconPosition.SECONDARY else None)
        self.cim.connect("activate", lambda _: self.megnyit())
        self.cim.connect("changed", lambda _: self.kieg_frissit())
        ck = Gtk.EventControllerKey()
        ck.connect("key-pressed", self.cim_billentyu)
        self.cim.add_controller(ck)
        cf = Gtk.EventControllerFocus()
        cf.connect("leave", lambda _: GLib.timeout_add(150, lambda: self.kieg.popdown() or False))
        self.cim.add_controller(cf)
        eh.append(self.cim)
        self.kieg_lista = Gtk.ListBox()
        self.kieg_lista.add_css_class("kieg")
        self.kieg_lista.connect("row-activated", lambda _, r: (self.cim.set_text(r.url), self.megnyit()))
        self.kieg = Gtk.Popover(child=self.kieg_lista, autohide=False, has_arrow=False, position=Gtk.PositionType.BOTTOM,
                                halign=Gtk.Align.START, can_focus=False)
        self.kieg.set_parent(self.cim)
        self.letolt_gomb = gomb("letoltes", self.letoltes_menu, "Letöltések")
        self.letolt_gomb.set_valign(Gtk.Align.CENTER)
        self.letolt_gomb.set_visible(False)
        eh.append(self.letolt_gomb)
        ph = Gtk.Box(spacing=6)
        self.pajzs_kep = kep("pajzs")
        self.pajzs_szam = Gtk.Label(label="0")
        ph.append(self.pajzs_kep)
        ph.append(self.pajzs_szam)
        self.pajzs = Gtk.Button(child=ph, valign=Gtk.Align.CENTER, tooltip_text="Blokkolás és adatvédelem ezen az oldalon")
        self.pajzs.add_css_class("pajzs")
        self.pajzs.connect("clicked", lambda _: self.pajzs_menu())
        eh.append(self.pajzs)
        jobb.append(self.eszkozsor)

        self.keresosav = Gtk.Box(spacing=4, margin_top=8, margin_bottom=8)
        self.keresosav.add_css_class("eszkozsor")
        self.keresomezo = Gtk.Entry(placeholder_text="Keresés az oldalon", width_request=320)
        self.keresomezo.connect("changed", lambda _: self.keres_lep(uj=True))
        self.keresomezo.connect("activate", lambda _: self.keres_lep(bool(self.billentyuzet_shift())))
        self.keresosav.append(self.keresomezo)
        for nev, fv in [("fel", lambda: self.keres_lep(True)), ("le", lambda: self.keres_lep()), ("x", self.keres_zar)]:
            self.keresosav.append(gomb(nev, fv))
        self.talalat = cimke("", "szam", margin_start=8)
        self.keresosav.append(self.talalat)
        self.keresosav.set_visible(False)
        jobb.append(self.keresosav)
        self.tolto = Gtk.ProgressBar()
        jobb.append(self.tolto)

        self.verem = Gtk.Stack(hexpand=True, vexpand=True)
        self.osztas = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=False, shrink_start_child=False, shrink_end_child=False)
        self.panelek = []
        for i in range(2):
            p = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
            csik = Gtk.Box()
            csik.add_css_class("csik")
            csik.set_visible(False)
            p.append(csik)
            tarto = self.verem if i == 0 else Gtk.Box(hexpand=True, vexpand=True)
            p.append(tarto)
            f = Gtk.EventControllerFocus()
            f.connect("enter", lambda _, i=i: self.fokusz_valt(i == 1))
            p.add_controller(f)
            self.panelek.append((p, tarto, csik))
        self.osztas.set_start_child(self.panelek[0][0])
        self.osztas.set_end_child(self.panelek[1][0])
        self.panelek[1][0].set_visible(False)
        self.reteg = Gtk.Overlay(child=self.osztas, vexpand=True)
        self.linkcimke = cimke("", "linkcimke", halign=Gtk.Align.START, valign=Gtk.Align.END, ellipsize=Pango.EllipsizeMode.MIDDLE,
                               can_target=False)
        self.linkcimke.set_visible(False)
        self.reteg.add_overlay(self.linkcimke)
        jobb.append(self.reteg)

        vezerlo = Gtk.ShortcutController(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        self.add_controller(vezerlo)
        for kulcs, fv in [
            ("<Control>t", lambda: self.uj_lap()),
            ("<Control><Shift>n", lambda: self.uj_lap(self.akt().identitas)),
            ("<Control><Shift>t", self.visszanyit),
            ("<Control>d", self.kj_hozzaad),
            ("<Control>k", self.parancssor),
            ("<Control>backslash", lambda: self.osztott_valt()),
            ("<Control>u", self.forras),
            ("<Control><Shift>c", self.link_masol),
            ("<Control><Shift>s", self.kepernyokep),
            ("<Control>w", lambda: self.bezar(self.lapok.index(self.akt()))),
            ("<Control>l", self.cimre),
            ("F6", self.cimre),
            ("<Control>Tab", lambda: self.sor_valaszt((self.akt_index() + 1) % len(self.lapok))),
            ("<Control><Shift>ISO_Left_Tab", lambda: self.sor_valaszt((self.akt_index() - 1) % len(self.lapok))),
            ("F5", lambda: self.akt().reload()), ("<Control>r", lambda: self.akt().reload()),
            ("<Alt>Left", lambda: self.akt().go_back()), ("<Alt>Right", lambda: self.akt().go_forward()),
            ("<Control><Shift>Delete", self.kiurit), ("<Control><Shift>o", self.tor_valt),
            ("<Control>f", self.keres), ("<Control><Shift>r", self.olvaso), ("<Control>m", lambda: self.nemit(self.akt())),
            ("F12", self.fejleszto),
            ("<Control>plus", lambda: self.nagyit(0.1)), ("<Control>equal", lambda: self.nagyit(0.1)),
            ("<Control>KP_Add", lambda: self.nagyit(0.1)), ("<Control>minus", lambda: self.nagyit(-0.1)),
            ("<Control>KP_Subtract", lambda: self.nagyit(-0.1)), ("<Control>0", lambda: self.nagyit(None)),
            ("<Control>p", self.pdf),
            ("<Control><Shift>l", self.uj_aramkor),
            ("<Control><Shift>u", self.felolvas),
            *[(f"<Control>{n}", lambda n=n: self.sor_valaszt(min(n, len(self.lapok)) - 1)) for n in range(1, 9)],
            ("<Control>9", lambda: self.sor_valaszt(len(self.lapok) - 1)),
        ]:
            vezerlo.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string(kulcs),
                                                  Gtk.CallbackAction.new(lambda *_, fv=fv: (fv(), True)[1])))
        vezerlo.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("Escape"),
                                              Gtk.CallbackAction.new(lambda *_: self.keres_zar() or True if self.keresosav.get_visible() else False)))

        self.connect("close-request", lambda _: self.leallit() or False)
        GLib.timeout_add_seconds(60, self.altat)
        self.kj_frissit()
        self.blokk.start()
        self.tor = None
        self.tor_szazalek = 100
        if TOR:
            self.tor_szazalek = 0
            self.tor = TorIndito(self.tor_allapot)
            self.tor.start()
        self.info_frissit()
        self.uj_lap()
        for a in [x for x in ARGS if not x.startswith("--")]:
            self.uj_lap(url=szuro.cim_ertelmez(a, KERESO))

    def billentyuzet_shift(self):
        return Gdk.Display.get_default().get_default_seat().get_keyboard().get_modifier_state() & Gdk.ModifierType.SHIFT_MASK

    def blokk_kesz(self):
        for lap in self.lapok:
            lap.send_message_to_page(WebKit.UserMessage.new("frissit", None), None, None, None)
        self.kozmetika()
        self.info_frissit()

    def kozmetika(self):
        ENGEDETT_F.write_text("\n".join(sorted(ENGEDETT)) + "\n")
        for idt in {lap.identitas for lap in self.lapok}:
            idt.kozmetika(self)
        for lap in self.lapok:
            lap.send_message_to_page(WebKit.UserMessage.new("frissit", None), None, None, None)

    def akt(self) -> Lap:
        return self.osztott if self.osztott and self.osztott_fokusz else self.verem.get_visible_child()

    def akt_index(self) -> int:
        return self.lapok.index(self.akt())

    def sor_valaszt(self, i):
        r = self.lista.get_row_at_index(i)
        if r:
            self.lista.select_row(r)

    def cimre(self):
        self.cim.grab_focus()
        self.cim.select_region(0, -1)

    def lista_katt(self, g, _, x, y):
        r = self.lista.get_row_at_y(int(y))
        if r is None:
            return
        gomb_ = g.get_current_button()
        if gomb_ == 2:
            self.bezar(r.get_index())
        elif gomb_ == 3:
            self.lap_menu(self.lapok[r.get_index()], x, y)

    def menu(self, horgony, tetelek, x=None, y=None):
        pop = Gtk.Popover(has_arrow=False, position=Gtk.PositionType.BOTTOM)
        doboz = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for t in tetelek:
            if t is None:
                doboz.append(Gtk.Separator())
            elif t[0] == "info":
                doboz.append(cimke(t[1], "info"))
            elif t[0] == "pipa":
                _, szoveg, be, fv = t
                cb = Gtk.CheckButton(label=szoveg, active=be)
                cb.connect("toggled", lambda c, fv=fv: (pop.popdown(), fv(c.get_active())))
                doboz.append(cb)
            else:
                szoveg, fv = t[0], t[1]
                b = Gtk.Button(child=Gtk.Label(label=szoveg, xalign=0), sensitive=len(t) < 3 or t[2])
                b.connect("clicked", lambda _, fv=fv: (pop.popdown(), GLib.idle_add(lambda: fv() and False)))
                doboz.append(b)
        pop.set_child(doboz)
        pop.set_parent(horgony)
        if x is not None:
            r = Gdk.Rectangle()
            r.x, r.y, r.width, r.height = int(x), int(y), 1, 1
            pop.set_pointing_to(r)
        pop.connect("closed", lambda p: GLib.idle_add(p.unparent))
        pop.popup()

    def kerdes(self, cim, szoveg, cb, igen="Igen"):
        d = Gtk.AlertDialog(message=cim, detail=szoveg, buttons=["Mégse", igen], cancel_button=0, default_button=1, modal=True)

        def kesz(d, r):
            try:
                cb(d.choose_finish(r) == 1)
            except GLib.Error:
                cb(False)

        d.choose(self, None, kesz)

    def uzen(self, cim, szoveg):
        Gtk.AlertDialog(message=cim, detail=szoveg, modal=True).show(self)

    def jelszo_ker(self, cim, szoveg, cb):
        w = Gtk.Window(title=cim, transient_for=self, modal=True, default_width=380, resizable=False)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        v.add_css_class("parbeszed")
        v.append(Gtk.Label(label=szoveg, xalign=0, wrap=True))
        e = Gtk.PasswordEntry(show_peek_icon=True, activates_default=True)
        v.append(e)
        h = Gtk.Box(spacing=8, halign=Gtk.Align.END)
        megse = Gtk.Button(label="Mégse")
        ok = Gtk.Button(label="OK")
        h.append(megse)
        h.append(ok)
        v.append(h)
        w.set_child(v)
        kesz = []

        def lezar(ertek):
            if not kesz:
                kesz.append(1)
                w.destroy()
                cb(ertek)

        megse.connect("clicked", lambda _: lezar(None))
        ok.connect("clicked", lambda _: lezar(e.get_text()))
        e.connect("activate", lambda _: lezar(e.get_text()))
        w.connect("close-request", lambda _: lezar(None) or False)
        w.present()

    def ment_ker(self, cim, ut: Path, cb):
        d = Gtk.FileDialog(title=cim, initial_name=ut.name, initial_folder=Gio.File.new_for_path(str(ut.parent)), modal=True)

        def kesz(d, r):
            try:
                f = d.save_finish(r)
                cb(f.get_path() if f else None)
            except GLib.Error:
                cb(None)

        d.save(self, None, kesz)

    def osztott_valt(self, lap=None):
        if self.osztott:
            regi = self.osztott
            self.osztott_ki()
            if lap is None or lap is regi:
                return
        bal = self.verem.get_visible_child()
        if lap is None or lap is bal:
            tobbi = [x for x in self.lapok if x is not bal]
            lap = max(tobbi, key=lambda x: x.utoljara) if tobbi else self.uj_lap(bal.identitas, hatterben=True)
        self.verem.remove(lap)
        p, tarto, _ = self.panelek[1]
        tarto.append(lap)
        p.set_visible(True)
        self.osztott = lap
        GLib.idle_add(lambda: self.osztas.set_position(self.osztas.get_width() // 2) and False)
        self.ebreszt(lap)
        if ures(lap.get_uri()):
            lap.uj_lap_oldal()
        self.fokusz_beallit(True)
        lap.grab_focus()

    def osztott_ki(self):
        lap, self.osztott = self.osztott, None
        self.panelek[1][0].set_visible(False)
        if lap in self.lapok:
            self.panelek[1][1].remove(lap)
            self.verem.add_child(lap)
            self.lap_frissult(lap)
        self.fokusz_beallit(False)

    def fokusz_beallit(self, jobb: bool):
        self.osztott_fokusz = jobb and self.osztott is not None
        for i, (_, _, csik) in enumerate(self.panelek):
            csik.set_visible(self.osztott is not None)
            (csik.add_css_class if (i == 1) == self.osztott_fokusz else csik.remove_css_class)("aktiv")
        lap = self.akt()
        if lap in self.lapok:
            self.csendes = True
            self.sor_valaszt(self.lapok.index(lap))
            self.csendes = False
            self.lap_frissult(lap)
            self.tolto_frissit(lap)

    def fokusz_valt(self, jobb):
        if self.osztott and jobb != self.osztott_fokusz:
            self.fokusz_beallit(jobb)

    def uj_lap(self, identitas=None, hatterben=False, url=None, rokon=None):
        lap = Lap(self, identitas or Identitas(self), rokon)
        self.lapok.append(lap)
        sor = LapSor(lap.identitas.szin)
        self.lista.append(sor)
        self.verem.add_child(lap)
        if url:
            lap.load_uri(url)
        elif not rokon:
            lap.uj_lap_oldal()
        if not hatterben:
            self.sor_valaszt(len(self.lapok) - 1)
            if not url and not rokon:
                GLib.idle_add(lambda: (self.cim.grab_focus(), self.cim.set_text("")) and False if lap is self.akt() else False)
        self.lap_frissult(lap)
        self.info_frissit()
        return lap

    def bezar(self, i):
        if i < 0 or i >= len(self.lapok):
            return
        lap = self.lapok.pop(i)
        if not ures(lap.get_uri()):
            self.bezartak = (self.bezartak + [(lap.get_uri(), lap.identitas)])[-20:]
        self.csendes = True
        self.lista.remove(self.lista.get_row_at_index(i))
        self.csendes = False
        if lap is self.osztott:
            self.osztott = None
            self.panelek[1][1].remove(lap)
            self.panelek[1][0].set_visible(False)
            self.fokusz_beallit(False)
        else:
            self.verem.remove(lap)
        lap.identitas.lapok -= 1
        lap.try_close()
        if not self.lapok:
            self.uj_lap()
        else:
            self.sor_valaszt(min(i, len(self.lapok) - 1))
        self.info_frissit()

    def ebreszt(self, lap):
        if lap.alszik:
            lap.alszik = False
            lap.reload()

    def valt(self, i):
        if not 0 <= i < len(self.lapok):
            return
        lap = self.lapok[i]
        lap.utoljara = time.monotonic()
        self.ebreszt(lap)
        if lap is self.osztott:
            lap.grab_focus()
        else:
            self.verem.set_visible_child(lap)
        if ures(lap.get_uri()) and not lap.is_loading():
            lap.uj_lap_oldal()
        self.fokusz_beallit(lap is self.osztott)
        self.lap_frissult(lap)

    def lap_frissult(self, lap):
        if lap not in self.lapok:
            return
        i = self.lapok.index(lap)
        sor = self.lista.get_row_at_index(i)
        u = lap.get_uri()
        u_ures = ures(u)
        if sor:
            hang = "osztva" if lap is self.osztott else "néma" if lap.get_is_muted() else "hang" if lap.is_playing_audio() else "alszik" if lap.alszik else ""
            sor.beallit("Új lap" if u_ures else lap.get_title() or u, sum(lap.blokkolva.values()), hang)
        if lap is self.akt():
            if not self.cim.has_focus() and not self.cim.get_focus_child():
                self.cim.set_text("" if u_ures else u)
            titkos = (u or "").startswith("https://") or u_ures
            self.cim.set_icon_from_paintable(Gtk.EntryIconPosition.PRIMARY, textura("lakat") if titkos else textura("nyitott", SZIN["lampa"]))
            self.cim.set_icon_tooltip_text(Gtk.EntryIconPosition.PRIMARY, "Titkosított kapcsolat" if titkos else "Titkosítatlan kapcsolat, ezen a lapon minden lehallgatható")
            ki = gazda(u) in ENGEDETT
            self.pajzs_szam.set_label("ki" if ki else str(sum(lap.blokkolva.values())))
            self.pajzs_kep.set_from_paintable(textura("pajzs", SZIN["lampa"] if ki else SZIN["masod"]))
            jelolt = self.szef.nyitva() and any(k["url"] == u for k in self.szef.lista)
            self.cim.set_icon_from_paintable(Gtk.EntryIconPosition.SECONDARY,
                                             None if u_ures else textura("csillag", SZIN["lampa"], True) if jelolt else textura("csillag"))
            self.set_title("Shade" if u_ures else f"{lap.get_title() or u} · Shade")

    def tolto_frissit(self, lap):
        if lap is self.akt():
            p = lap.get_estimated_load_progress()
            self.tolto.set_fraction(0 if p >= 1 or not lap.is_loading() else p)

    def link_mutat(self, lap, u):
        if not u or not lap.get_mapped():
            self.linkcimke.set_visible(False)
            return
        ok, pont = lap.compute_point(self.reteg, Graphene.Point().init(0, 0))
        self.linkcimke.set_margin_start(int(pont.x) if ok else 0)
        self.linkcimke.set_max_width_chars(max(30, lap.get_width() // 16))
        self.linkcimke.set_label(u)
        self.linkcimke.set_visible(True)

    def megnyit(self):
        self.kieg.popdown()
        s = self.cim.get_text().strip()
        if s:
            self.akt().load_uri(szuro.cim_ertelmez(s, KERESO))
            self.akt().grab_focus()

    def kieg_frissit(self):
        if not self.cim.has_focus() and not self.cim.get_focus_child():
            return
        s = self.cim.get_text().strip().lower()
        tetelek = [k["url"] for k in self.szef.lista] + [x.get_uri() for x in self.lapok]
        talalt = [t for t in dict.fromkeys(t for t in tetelek if not ures(t)) if s and s in t.lower() and t.lower() != s][:8]
        while (r := self.kieg_lista.get_row_at_index(0)) is not None:
            self.kieg_lista.remove(r)
        for t in talalt:
            r = Gtk.ListBoxRow(child=Gtk.Label(label=t, xalign=0, ellipsize=Pango.EllipsizeMode.END, max_width_chars=80))
            r.url = t
            self.kieg_lista.append(r)
        if talalt:
            self.kieg.set_size_request(self.cim.get_width(), -1)
            self.kieg.popup()
        else:
            self.kieg.popdown()

    def cim_billentyu(self, _, kulcs, __, ___):
        if not self.kieg.get_visible():
            return False
        if kulcs in (Gdk.KEY_Down, Gdk.KEY_Up):
            r = self.kieg_lista.get_selected_row()
            i = (r.get_index() if r else -1) + (1 if kulcs == Gdk.KEY_Down else -1)
            uj = self.kieg_lista.get_row_at_index(max(0, i))
            if uj:
                self.kieg_lista.select_row(uj)
                self.cim.set_text(uj.url)
                self.cim.set_position(-1)
            return True
        if kulcs == Gdk.KEY_Escape:
            self.kieg.popdown()
            return True
        return False

    def info_frissit(self):
        if TOR:
            self.mod.set_label("tor" if self.tor_szazalek >= 100 else f"tor {self.tor_szazalek}%")
        else:
            self.mod.set_label("közvetlen")
        self.allapot["Tiltólista"].set_label(f"{len(self.blokk.lista):,}".replace(",", " "))
        self.allapot["DNS"].set_label("Tor-láncon" if TOR else "rendszer")
        self.allapot["Szint"].set_label(SZINTEK[self.szint].lower())
        self.allapot["Identitás"].set_label(f"{len({id(x.identitas) for x in self.lapok})} ({len(self.lapok)} lap)")

    def tor_allapot(self, sz):
        if sz < 0:
            self.uzen("Tor", "A tor nincs telepítve. Telepítés: sudo pacman -S tor" if sz == -1 else "A tor leállt, mielőtt kapcsolódott volna. Most semmi nem megy ki a hálózatra.")
            sz = 0
        self.tor_szazalek = sz
        self.info_frissit()

    def tor_valt(self):
        def tovabb(igen):
            if igen:
                uj = [a for a in ARGS if a != "--tor"] + ([] if TOR else ["--tor"])
                self.leallit()
                os.execv(sys.executable, [sys.executable, str(MAPPA / "shade.py")] + uj)

        self.kerdes("Mód váltása", "A váltás minden lapot és identitást töröl. Mehet?", tovabb)

    def kiurit(self):
        if self.osztott:
            self.osztott_ki()
        self.csendes = True
        while self.lapok:
            lap = self.lapok.pop()
            self.lista.remove(self.lista.get_row_at_index(len(self.lapok)))
            self.verem.remove(lap)
            lap.try_close()
        self.csendes = False
        self.munkamenet.clear()
        self.bezartak.clear()
        self.nagyitas.clear()
        self.szef.zar()
        self.kj_frissit()
        self.get_clipboard().set_content(None)
        Gdk.Display.get_default().get_primary_clipboard().set_content(None)
        Identitas.szamlalo = 0
        self.uj_lap()
        self.info_frissit()

    def pajzs_menu(self):
        lap = self.akt()
        host = gazda(lap.get_uri())
        t = [("info", f"{d}   {c}") for d, c in lap.blokkolva.most_common(8)] or [("info", "Ezen az oldalon nem volt mit blokkolni")]
        t.append(None)
        if host:
            t.append(("pipa", f"Blokkolás itt: {host}", host not in ENGEDETT,
                      lambda be: (ENGEDETT.discard(host) if be else ENGEDETT.add(host), self.kozmetika(), lap.reload())))
        t.append(("info", "Biztonsági szint"))
        for i, nev in enumerate(SZINTEK):
            t.append(("pipa", nev + ["", ": WebGL ki, http-n JavaScript ki", ": JavaScript és WebGL mindenhol ki"][i], self.szint == i,
                      lambda _, i=i: self.szint_allit(i)))
        t.append(None)
        t.append(("pipa", "Sötét mód minden oldalon", self.sotet, lambda _: self.sotet_valt()))
        t.append(("pipa", "JavaScript ebben az identitásban", lap.identitas.js,
                  lambda be: (setattr(lap.identitas, "js", be), lap.reload())))
        t.append(None)
        t.append(("Sütik és gyorsítótár törlése ebben az identitásban", lambda: lap.identitas.munkamenet.get_website_data_manager().clear(
            WebKit.WebsiteDataTypes.ALL, 0, None, lambda *_: lap.reload())))
        t.append(("Megnyitás új identitásban", lambda: self.uj_lap(url=lap.get_uri())))
        self.menu(self.pajzs, t)

    def nemit(self, lap):
        lap.set_is_muted(not lap.get_is_muted())

    def lap_menu(self, lap, x, y):
        self.menu(self.lista, [
            ("Hang vissza" if lap.get_is_muted() else "Némítás", lambda: self.nemit(lap)),
            ("Újra új identitásban", lambda: self.uj_lap(url=lap.get_uri())),
            ("Lap ugyanebben az identitásban", lambda: self.uj_lap(lap.identitas)),
            ("Duplikálás", lambda: self.uj_lap(lap.identitas, url=lap.get_uri())),
            ("Osztott nézet bezárása" if lap is self.osztott else "Megnyitás osztott nézetben", lambda: self.osztott_valt(lap)),
            None,
            ("Bezárás", lambda: self.bezar(self.lapok.index(lap))),
            ("Többi bezárása", lambda: [self.bezar(self.lapok.index(x)) for x in list(self.lapok) if x is not lap]),
        ], x, y)

    def parancssor(self):
        t = [("lap", x.get_title() or x.get_uri() or "Új lap", lambda x=x: self.sor_valaszt(self.lapok.index(x))) for x in self.lapok]
        t += [("könyvjelző", k["cim"], lambda k=k: self.akt().load_uri(k["url"])) for k in self.szef.lista]
        t += [("parancs", nev, fv) for nev, fv in [
            ("Új identitás", lambda: self.uj_lap()),
            ("Lap ugyanebben az identitásban", lambda: self.uj_lap(self.akt().identitas)),
            ("Bezárt lap vissza", self.visszanyit),
            ("Könyvjelző be/ki", self.kj_hozzaad),
            ("Könyvjelzők feloldása" if not self.szef.nyitva() else "Könyvjelzők lezárása",
             lambda: self.kj_felold(self.kj_frissit) if not self.szef.nyitva() else (self.szef.zar(), self.kj_frissit())),
            ("Osztott nézet be/ki", lambda: self.osztott_valt()),
            ("Olvasó mód", self.olvaso),
            ("Felolvasás be/ki", self.felolvas),
            ("Sötét mód minden oldalon be/ki", self.sotet_valt),
            *[(f"Biztonsági szint: {n}", lambda i=i: self.szint_allit(i)) for i, n in enumerate(SZINTEK)],
            ("Új Tor-útvonal és új identitás", self.uj_aramkor),
            ("Keresés az oldalon", self.keres),
            ("Mentés PDF-be", self.pdf),
            ("Képernyőkép", self.kepernyokep),
            ("Oldal forrása", self.forras),
            ("Link másolása", self.link_masol),
            ("Némítás be/ki", lambda: self.nemit(self.akt())),
            ("Letöltések", self.letoltes_menu),
            ("Fejlesztői eszközök", self.fejleszto),
            ("Kiürítés", self.kiurit),
            ("Kilépés a Torból" if TOR else "Tor mód", self.tor_valt),
        ]]
        w = Gtk.Window(transient_for=self, modal=True, decorated=False, default_width=560, resizable=False)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        v.add_css_class("parancssor")
        mezo = Gtk.SearchEntry(placeholder_text="Lap, könyvjelző vagy parancs")
        lista = Gtk.ListBox()
        gorgo = Gtk.ScrolledWindow(child=lista, hscrollbar_policy=Gtk.PolicyType.NEVER, propagate_natural_height=True, max_content_height=8 * 38)
        v.append(mezo)
        v.append(gorgo)
        w.set_child(v)
        talalt = []

        def szur(*_):
            szavak = mezo.get_text().lower().split()
            talalt[:] = [x for x in t if all(sz in (x[0] + " " + x[1]).lower() for sz in szavak)]
            while (r := lista.get_row_at_index(0)) is not None:
                lista.remove(r)
            for fajta, cim_, _ in talalt:
                h = Gtk.Box(spacing=12)
                h.append(cimke(cim_, "lapcim", hexpand=True, ellipsize=Pango.EllipsizeMode.END))
                h.append(cimke(fajta, "szam"))
                lista.append(Gtk.ListBoxRow(child=h))
            gorgo.set_visible(bool(talalt))
            lista.select_row(lista.get_row_at_index(0))

        def futtat(*_):
            r = lista.get_selected_row()
            if r and r.get_index() < len(talalt):
                fv = talalt[r.get_index()][2]
                w.destroy()
                GLib.idle_add(lambda: fv() and False)

        def billentyu(_, kulcs, *__):
            if kulcs in (Gdk.KEY_Down, Gdk.KEY_Up):
                r = lista.get_selected_row()
                i = (r.get_index() if r else 0) + (1 if kulcs == Gdk.KEY_Down else -1)
                uj = lista.get_row_at_index(max(0, min(len(talalt) - 1, i)))
                if uj:
                    lista.select_row(uj)
                return True
            if kulcs == Gdk.KEY_Escape:
                w.destroy()
                return True
            return False

        mezo.connect("search-changed", szur)
        mezo.connect("activate", futtat)
        lista.connect("row-activated", futtat)
        k = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        k.connect("key-pressed", billentyu)
        w.add_controller(k)
        szur()
        w.present()
        mezo.grab_focus()

    def kj_felold(self, utana):
        if self.szef.nyitva():
            utana()
            return
        uj = not self.szef.letezik()
        cim = "Könyvjelzők létrehozása" if uj else "Könyvjelzők feloldása"

        def probal(jelszo):
            try:
                self.szef.felold(jelszo)
            except konyvjelzo.RosszJelszo as h:
                self.uzen(cim, str(h))
                return
            utana()

        def elso(jelszo):
            if not jelszo:
                return
            if not uj:
                probal(jelszo)
                return
            self.jelszo_ker(cim, "Jelszó még egyszer:",
                            lambda ujra: probal(jelszo) if ujra == jelszo else (self.uzen(cim, "A két jelszó nem egyezik") if ujra is not None else None))

        self.jelszo_ker(cim, "Jelszó (titkosítva tárolja, csak ezzel nyílik):" if uj else "Jelszó:", elso)

    def kj_frissit(self):
        nyitva = self.szef.nyitva()
        while (r := self.kj_lista.get_row_at_index(0)) is not None:
            self.kj_lista.remove(r)
        for k in self.szef.lista:
            r = Gtk.ListBoxRow(child=cimke(k["cim"], "lapcim", ellipsize=Pango.EllipsizeMode.END), tooltip_text=k["url"])
            r.url = k["url"]
            self.kj_lista.append(r)
        self.kj_gorgo.set_visible(nyitva and bool(self.szef.lista))
        self.kj_nyit.set_visible(not nyitva)
        self.kj_nyit.cimke.set_label("Feloldás" if self.szef.letezik() else "Bekapcsolás")
        if self.lapok:
            self.lap_frissult(self.akt())

    def kj_hozzaad(self):
        lap = self.akt()
        url = lap.get_uri()
        if ures(url):
            return

        def tovabb():
            meglevo = [i for i, k in enumerate(self.szef.lista) if k["url"] == url]
            if meglevo:
                self.szef.torol(meglevo[0])
            else:
                self.szef.hozzaad(lap.get_title() or url, url)
            self.kj_frissit()

        self.kj_felold(tovabb)

    def kj_menu(self, g, _, x, y):
        r = self.kj_lista.get_row_at_y(int(y))
        if not r:
            return
        i, url = r.get_index(), r.url
        self.menu(self.kj_lista, [
            ("Megnyitás új identitásban", lambda: self.uj_lap(url=url)),
            ("Törlés", lambda: (self.szef.torol(i), self.kj_frissit())),
            None,
            ("Lezárás", lambda: (self.szef.zar(), self.kj_frissit())),
        ], x, y)

    def visszanyit(self):
        if not self.bezartak:
            return
        url, idt = self.bezartak.pop()
        self.uj_lap(idt if idt.lapok > 0 else None, url=url)

    def jelzes(self, szoveg):
        self.linkcimke.set_margin_start(0)
        self.linkcimke.set_label(szoveg)
        self.linkcimke.set_visible(True)
        GLib.timeout_add(1500, lambda: self.linkcimke.set_visible(False) or False)

    def link_masol(self):
        self.get_clipboard().set(self.akt().get_uri() or "")
        self.jelzes("Link vágólapra másolva")

    def kepernyokep(self):
        lap = self.akt()
        alap = Path.home() / "Képek"
        nev = re.sub(r"[^\w.-]+", "-", gazda(lap.get_uri()) or "lap") + time.strftime("-%Y%m%d-%H%M%S.png")

        def ment(ut):
            if ut:
                lap.get_snapshot(WebKit.SnapshotRegion.VISIBLE, WebKit.SnapshotOptions.NONE, None,
                                 lambda l, r: l.get_snapshot_finish(r).save_to_png(ut))

        self.ment_ker("Képernyőkép mentése", (alap if alap.exists() else Path.home()) / nev, ment)

    def forras(self):
        lap = self.akt()
        res = lap.get_main_resource()
        if not res:
            return

        def kesz(r, eredmeny):
            try:
                adat = r.get_data_finish(eredmeny)
            except GLib.Error:
                return
            uj = self.uj_lap(lap.identitas, rokon=None, url=None)
            uj.load_plain_text(bytes(adat).decode(errors="replace"))

        res.get_data(None, kesz)

    def nagyit(self, lepes):
        lap = self.akt()
        z = 1.0 if lepes is None else min(5.0, max(0.3, round(lap.get_zoom_level() + lepes, 2)))
        h = gazda(lap.get_uri())
        if h:
            self.nagyitas[h] = z
        for x in self.lapok:
            if x is lap or (h and gazda(x.get_uri()) == h):
                x.set_zoom_level(z)

    def altat(self):
        most = time.monotonic()
        for lap in self.lapok:
            if (lap is not self.akt() and lap is not self.osztott and most - lap.utoljara > 10 * 60 and not lap.is_playing_audio()
                    and not lap.alszik and not ures(lap.get_uri())):
                lap.alszik = True
                lap.terminate_web_process()
                self.lap_frissult(lap)
        return True

    def olvaso(self):
        self.akt().evaluate_javascript((MAPPA / "olvaso.js").read_text(), -1, "shade", None, None, None)

    def pdf(self):
        lap = self.akt()

        def ment(ut):
            if not ut:
                return
            nyomtato = []
            Gtk.enumerate_printers(lambda p, *_: (nyomtato.append(p.get_name()) if p.is_virtual() and p.accepts_pdf() else None) or False, True)
            ps = Gtk.PrintSettings()
            ps.set_printer(nyomtato[0] if nyomtato else "Print to File")
            ps.set("output-file-format", "pdf")
            ps.set("output-uri", Gio.File.new_for_path(ut).get_uri())
            op = WebKit.PrintOperation.new(lap)
            op.set_print_settings(ps)
            op.print_()

        self.ment_ker("Mentés PDF-be", Path.home() / "lap.pdf", ment)

    def keres(self):
        self.keresosav.set_visible(True)
        self.keresomezo.grab_focus()
        self.keresomezo.select_region(0, -1)
        self.keres_lep(uj=True)

    def keres_lep(self, vissza=False, uj=False):
        szoveg = self.keresomezo.get_text()
        fc = self.akt().get_find_controller()
        if not szoveg:
            fc.search_finish()
            self.talalat.set_label("")
            return
        if uj or fc.get_search_text() != szoveg:
            o = WebKit.FindOptions.CASE_INSENSITIVE | WebKit.FindOptions.WRAP_AROUND
            fc.count_matches(szoveg, o, 1000)
            fc.search(szoveg, o, 1000)
        elif vissza:
            fc.search_previous()
        else:
            fc.search_next()

    def talalat_jelez(self, lap, n):
        if lap is self.akt() and self.keresosav.get_visible():
            self.talalat.set_label(f"{n} találat" if n else "nincs találat")

    def keres_zar(self):
        self.keresosav.set_visible(False)
        self.akt().get_find_controller().search_finish()
        self.akt().grab_focus()

    def szint_allit(self, szint):
        self.szint = szint
        self.info_frissit()
        for lap in self.lapok:
            lap.reload()

    def sotet_valt(self):
        self.sotet = not self.sotet
        for idt in {lap.identitas for lap in self.lapok}:
            idt.kozmetika(self)

    def uj_aramkor(self):
        if not TOR:
            self.uzen("Új Tor-útvonal", "Ez csak Tor módban működik (Ctrl+Shift+O)")
            return
        suti = CACHE / "tor" / "control_auth_cookie"
        try:
            with socket.create_connection(("127.0.0.1", TOR_PORT + 1), timeout=5) as s:
                s.sendall(f"AUTHENTICATE {suti.read_bytes().hex()}\r\nSIGNAL NEWNYM\r\nQUIT\r\n".encode())
                valasz = s.recv(1024).decode(errors="ignore")
        except OSError as h:
            self.uzen("Új Tor-útvonal", f"A Tor vezérlője nem érhető el ({h}). Csak a saját indítású Torral megy, a rendszer-Torral nem.")
            return
        if valasz.count("250") < 2:
            self.uzen("Új Tor-útvonal", "A Tor nem fogadta el a kérést")
            return
        url = self.akt().get_uri()
        self.uj_lap(url=None if ures(url) else url)

    def felolvas(self):
        if any(p.poll() is None for p in self.felolvaso):
            for p in self.felolvaso:
                p.kill()
            self.felolvaso = []
            return
        if not (Path(PIPER).exists() and Path(PIPER_HANG).exists()):
            self.uzen("Felolvasás", f"Nincs meg a Piper vagy a hang.\nSHADE_PIPER={PIPER}\nSHADE_HANG={PIPER_HANG}")
            return
        js = ("(()=>{const k=String(getSelection()).trim();if(k)return k;"
              "const e=document.querySelector('article,main,[role=main]')||document.body;return e.innerText})()")

        def indit(lap, r):
            try:
                szoveg = lap.evaluate_javascript_finish(r).to_string()
            except GLib.Error:
                return
            szoveg = re.sub(r"\s+", " ", szoveg or "").strip()[:8000]
            if not szoveg:
                return
            piper = subprocess.Popen([PIPER, "--model", PIPER_HANG, "--output-raw"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            lejatszo = subprocess.Popen(["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-c", "1"], stdin=piper.stdout)
            piper.stdout.close()
            piper.stdin.write(szoveg.encode())
            piper.stdin.close()
            self.felolvaso = [piper, lejatszo]

        self.akt().evaluate_javascript(js, -1, "shade", None, None, indit)

    def fejleszto(self):
        self.akt().get_inspector().show()

    def teljes_kepernyo(self, be):
        for w in (self.oldalsav, self.eszkozsor, self.tolto):
            w.set_visible(not be)
        self.fullscreen() if be else self.unfullscreen()

    def letoltes(self, _, d):
        alap = Path.home() / "Letöltések"
        if not alap.exists():
            alap = Path.home() / "Downloads"
        t = {"nev": "", "ut": "", "szazalek": 0, "allapot": "fut", "hiba": False}

        def cel(d, javasolt):
            def kesz(ut):
                if not ut:
                    d.cancel()
                    return
                t["nev"], t["ut"] = Path(ut).name, ut
                d.set_allow_overwrite(True)
                d.set_destination(ut)
                self.letoltesek.insert(0, t)
                self.letolt_gomb.set_visible(True)
                for w in self.letoltes_sor:
                    w.set_visible(True)
                self.allapot["Letöltés"].set_tooltip_text(t["nev"])

            self.ment_ker("Letöltés mentése", alap / (javasolt or "letoltes"), kesz)
            return True

        def halad(*_):
            t["szazalek"] = int(d.get_estimated_progress() * 100)
            self.allapot["Letöltés"].set_label(f"{t['szazalek']}%")

        def vege(_):
            if t not in self.letoltesek:
                return
            t["allapot"] = "hiba" if t["hiba"] else "kesz"
            if not any(x["allapot"] == "fut" for x in self.letoltesek):
                for w in self.letoltes_sor:
                    w.set_visible(False)
            subprocess.Popen(["notify-send", "-a", "Shade", "--", "A letöltés megszakadt" if t["hiba"] else "Letöltve", t["nev"]])

        d.connect("decide-destination", cel)
        d.connect("notify::estimated-progress", halad)
        d.connect("failed", lambda *_: t.update(hiba=True))
        d.connect("finished", vege)

    def letoltes_torles(self):
        self.letoltesek = [x for x in self.letoltesek if x["allapot"] == "fut"]
        self.letolt_gomb.set_visible(bool(self.letoltesek))

    def megnyit_fajl(self, ut, mappa=False):
        l = Gtk.FileLauncher.new(Gio.File.new_for_path(ut))
        l.open_containing_folder(self, None, None) if mappa else l.launch(self, None, None)

    def letoltes_menu(self):
        t = []
        for x in self.letoltesek[:10]:
            allapot = {"fut": f"{x['szazalek']}%", "kesz": "kész", "hiba": "megszakadt"}[x["allapot"]]
            t.append((f"{x['nev'][:40]}    {allapot}", lambda x=x: self.megnyit_fajl(x["ut"]), x["allapot"] == "kesz"))
        t.append(None)
        if self.letoltesek:
            t.append(("Mappa megnyitása", lambda: self.megnyit_fajl(self.letoltesek[0]["ut"], True)))
        t.append(("Lista törlése", self.letoltes_torles))
        self.menu(self.letolt_gomb, t)

    def kezdolap(self, idt: Identitas) -> str:
        osszes = sum(self.munkamenet.values())
        top = self.munkamenet.most_common(5)
        maxi = top[0][1] if top else 1
        sorok = "".join(
            f'<li><span class="d">{html.escape(d)}</span><span class="n">{n}</span>'
            f'<i><b style="width:{max(2, n * 100 // maxi)}%;{"background:" + SZIN["lampa"] if j == 0 else ""}"></b></i></li>'
            for j, (d, n) in enumerate(top)
        ) or '<li class="ures">Ebben a munkamenetben még semmi nem próbált követni</li>'
        halo = "Tor-hálózat, három ugrás" if TOR else "Közvetlen, a rendszer DNS-ével"
        kereso = html.escape(KERESO.split("?")[0])
        return f"""<!doctype html><html lang="hu"><head><meta charset="utf-8"><title>Új lap</title><style>
:root{{color-scheme:dark;--e:cubic-bezier(.22,1,.36,1)}}
*{{box-sizing:border-box;margin:0}}
body{{background:{SZIN['hatter']};color:{SZIN['szoveg']};font:14px/20px Inter,sans-serif;min-height:100vh;display:grid;place-items:center;padding:48px 32px}}
main{{width:min(960px,100%);animation:be .4s var(--e) both}}
@keyframes be{{from{{opacity:0;transform:translateY(8px)}}}}
@media(prefers-reduced-motion:reduce){{main{{animation:none}}}}
form{{position:relative;margin-bottom:48px}}
form svg{{position:absolute;left:16px;top:16px;width:16px;height:16px;stroke:{SZIN['halk']}}}
input{{width:100%;height:48px;background:{SZIN['felulet']};border:1px solid {SZIN['vonal']};border-radius:12px;color:inherit;font:inherit;font-size:15px;padding:0 16px 0 44px;outline:none;transition:border-color .15s var(--e),background-color .15s var(--e)}}
input::placeholder{{color:{SZIN['halk']}}}
input:focus{{background:{SZIN['emelt']};border-color:rgba(237,237,237,.2)}}
.fo{{display:grid;grid-template-columns:320px 1fr;gap:48px;align-items:center}}
.nyomat{{background:{SZIN['mely']};border:1px solid {SZIN['vonal']};border-radius:16px;padding:32px;aspect-ratio:1;display:grid;place-items:center}}
.nyomat svg{{width:100%;height:100%}}
.cimsor{{display:flex;align-items:center;gap:12px;margin-bottom:8px}}
.pont{{width:10px;height:10px;border-radius:5px;background:{idt.szin}}}
h1{{font-size:32px;line-height:40px;font-weight:500}}
.mag{{font-family:'JetBrains Mono',monospace;font-size:12px;color:{SZIN['halk']};margin-bottom:24px}}
dl{{display:grid;grid-template-columns:112px 1fr;row-gap:12px;border-top:1px solid {SZIN['vonal']};padding-top:24px}}
dt{{color:{SZIN['halk']}}}
dd{{color:{SZIN['masod']}}}
.blokk{{margin-top:48px;border-top:1px solid {SZIN['vonal']};padding-top:24px;display:grid;grid-template-columns:320px 1fr;gap:48px}}
.szam{{font-family:'JetBrains Mono',monospace;font-size:32px;line-height:1;font-variant-numeric:tabular-nums;margin-bottom:8px}}
.al{{color:{SZIN['halk']}}}
ul{{list-style:none;padding:0;display:grid;gap:12px}}
li{{display:grid;grid-template-columns:1fr auto;row-gap:4px}}
li .d{{color:{SZIN['masod']};overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
li .n{{font-family:'JetBrains Mono',monospace;font-size:12px;color:{SZIN['halk']};font-variant-numeric:tabular-nums}}
li i{{grid-column:1/3;height:4px;border-radius:2px;background:{SZIN['felulet']};display:block}}
li b{{display:block;height:100%;border-radius:2px;background:#3a3a3d}}
li.ures{{display:block;color:{SZIN['halk']}}}
footer{{margin-top:48px;color:{SZIN['halk']};font-size:12px;display:flex;gap:8px 24px;flex-wrap:wrap}}
kbd{{font-family:'JetBrains Mono',monospace;font-size:11px;border:1px solid rgba(237,237,237,.14);border-bottom-width:2px;border-radius:4px;padding:0 4px;color:{SZIN['masod']};margin-right:2px}}
@media(max-width:760px){{.fo,.blokk{{grid-template-columns:1fr;gap:24px}}.nyomat{{max-width:240px}}}}
</style></head><body><main>
<form action="{kereso}" method="get"><svg viewBox="0 0 24 24" fill="none" stroke-width="1.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg><input name="q" placeholder="Keresés" autofocus autocomplete="off"></form>
<div class="fo">
<div class="nyomat">{ujjlenyomat_svg(idt.mag, idt.szin)}</div>
<div><div class="cimsor"><span class="pont"></span><h1>Identitás {idt.nev}</h1></div>
<div class="mag">mag {idt.mag} · bezáráskor nyomtalanul eltűnik</div>
<dl>
<dt>Motor</dt><dd>WebKit, nem Chromium</dd>
<dt>Sütik</dt><dd>Csak ez az identitás látja őket</dd>
<dt>Ujjlenyomat</dt><dd>Vászon és hang zajosítva, ez a mintája</dd>
<dt>Hálózat</dt><dd>{halo}</dd>
<dt>WebRTC</dt><dd>{"Kikapcsolva, csak Toron át mehetne" if TOR else "Helyi cím csak engedély után látszik"}</dd>
<dt>Lemez</dt><dd>Nincs előzmény, nincs gyorsítótár</dd>
</dl></div>
</div>
<div class="blokk"><div><div class="szam">{osszes}</div><div class="al">blokkolt kérés ebben a munkamenetben, {len(self.munkamenet)} követőtől</div></div>
<ul>{sorok}</ul></div>
<footer><span><kbd>Ctrl</kbd><kbd>T</kbd> új identitás</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>N</kbd> lap ugyanebben</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>T</kbd> bezárt lap vissza</span><span><kbd>Ctrl</kbd><kbd>D</kbd> könyvjelző</span><span><kbd>Ctrl</kbd><kbd>K</kbd> parancsok</span><span><kbd>Ctrl</kbd><kbd>\\</kbd> osztott nézet</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>Del</kbd> kiürítés</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>R</kbd> olvasó</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>O</kbd> Tor</span></footer>
</main></body></html>"""

    def leallit(self):
        for p in self.felolvaso:
            p.kill()
        if self.tor and self.tor.folyamat:
            self.tor.folyamat.terminate()


def main():
    if not TILTOTT_F.exists():
        TILTOTT_F.write_text("\n".join(sorted(szuro.ALAP_TILTOTT)) + "\n")
    ENGEDETT_F.write_text("")
    ctx = WebKit.WebContext.get_default()
    mappa = kiterjesztes()
    if mappa:
        ctx.set_web_process_extensions_directory(str(mappa))
        ctx.set_web_process_extensions_initialization_user_data(GLib.Variant("(ss)", (str(TILTOTT_F), str(ENGEDETT_F))))
    ctx.add_path_to_sandbox(str(CACHE), True)
    ctx.set_preferred_languages(["hu-HU", "hu", "en"])
    ctx.set_spell_checking_enabled(False)
    ctx.set_cache_model(WebKit.CacheModel.WEB_BROWSER)
    GLib.set_prgname("shade")
    GLib.set_application_name("Shade")
    app = Gtk.Application(flags=Gio.ApplicationFlags.NON_UNIQUE)

    def indul(app):
        css = Gtk.CssProvider()
        css.load_from_string(stilus())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        Gtk.Settings.get_default().set_property("gtk-interface-color-scheme", Gtk.InterfaceColorScheme.DARK)
        Gtk.Window.set_default_icon_name("shade")
        app.ablak = Ablak(app)
        app.ablak.present()

    app.connect("activate", indul)
    app.connect("shutdown", lambda a: getattr(a, "ablak", None) and a.ablak.leallit())
    sys.exit(app.run([sys.argv[0]]))


if __name__ == "__main__":
    main()
