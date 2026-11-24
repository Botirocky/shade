import glob
import html
import math
import random
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import szuro

MAPPA = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "arnyek"
ADAT = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "arnyek"
HOSTS_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
EASYLIST_URL = "https://easylist.to/easylist/easylist.txt"
HUFILTER_URL = "https://raw.githubusercontent.com/hufilter/hufilter/gh-pages/hufilter.txt"
KERESO = os.environ.get("ARNYEK_KERESO", "https://duckduckgo.com/?q={}")
DOH = os.environ.get("ARNYEK_DOH", "https://dns.mullvad.net/dns-query")
ARGS = sys.argv[1:]
TOR = "--tor" in ARGS
RENDSZER_DNS = "--rendszer-dns" in ARGS
HELYI_ZONAK = os.environ.get("ARNYEK_HELYI", "nagy.park.lan park.lan").split()
ENGEDETT: set[str] = set()
if TOR:
    os.environ["TZ"] = "UTC"


def helyi_szabalyok() -> list[str]:
    talalt = {}

    def proba(z):
        try:
            talalt[z] = socket.getaddrinfo(z, 80, socket.AF_INET)[0][4][0]
        except OSError:
            pass

    szalak = [threading.Thread(target=proba, args=(z,), daemon=True) for z in HELYI_ZONAK]
    for t in szalak:
        t.start()
    hatarido = time.time() + 1.5
    for t in szalak:
        t.join(max(0, hatarido - time.time()))
    return [f"MAP *.{z} {talalt[z]}, MAP {z} {talalt[z]}" for z in HELYI_ZONAK if z in talalt]


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


def chromium_flagek() -> list[str]:
    f = [
        "--force-webrtc-ip-handling-policy=" + ("disable_non_proxied_udp" if TOR else "default_public_interface_only"),
        "--no-pings",
        "--disable-breakpad",
        "--disable-domain-reliability",
        "--disable-background-networking",
        "--disable-features=BrowsingTopics,Fledge,InterestGroupStorage,PrivacySandboxAdsAPIs,"
        "AttributionReportingCrossAppWeb,ConversionMeasurement,InterestFeedContentSuggestions,MediaRouter",
    ]
    wv = (
        glob.glob("/usr/lib/chromium/WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so")
        + glob.glob("/opt/google/chrome/WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so")
        + sorted(glob.glob(str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so")))
    )
    sajat = ADAT / "WidevineCdm/_platform_specific/linux_x64/libwidevinecdm.so"
    if wv and not sajat.exists():
        try:
            shutil.copytree(Path(wv[-1]).parents[2], ADAT / "WidevineCdm", dirs_exist_ok=True)
        except OSError:
            pass
    if sajat.exists() or wv:
        f.append(f"--widevine-path={sajat if sajat.exists() else wv[-1]}")
    if TOR:
        f += [
            f"--proxy-server=socks5://127.0.0.1:{TOR_PORT}",
            "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
            "--disable-quic",
        ]
    elif not RENDSZER_DNS:
        sz = helyi_szabalyok()
        if sz:
            f.append("--host-resolver-rules=" + ", ".join(sz))
    return f

from PySide6.QtCore import QByteArray, QSize, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QGuiApplication, QIcon, QKeySequence, QPainter, QPalette, QPixmap, QShortcut
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWebEngineCore import (
    QWebEngineDownloadRequest, QWebEngineGlobalSettings, QWebEnginePage, QWebEnginePermission,
    QWebEngineProfile, QWebEngineScript, QWebEngineSettings, QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QMenu, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton, QStackedWidget, QToolButton,
    QVBoxLayout, QWidget,
)

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
    "radir": '<path d="m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21"/><path d="M22 21H7"/><path d="m5 11 9 9"/>',
}


def ikon(nev: str, szin: str = SZIN["masod"], meret: int = 16) -> QIcon:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{szin}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{IKON[nev]}</svg>'
    dpr = 2
    pm = QPixmap(meret * dpr, meret * dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return QIcon(pm)


class Blokklista(QThread):
    betoltve = Signal(int)

    def __init__(self):
        super().__init__()
        self.lista = set(szuro.ALAP_TILTOTT)
        self.css = ""
        self.oldal: dict[str, list[str]] = {}
        self.kivetel: dict[str, set[str]] = {}

    def run(self):
        try:
            adat = self.friss("hosts.txt", HOSTS_URL, lambda a: len(szuro.hosts_beolvas(a)) > 1000)
            if adat:
                self.lista = set(szuro.ALAP_TILTOTT) | szuro.hosts_beolvas(adat)
                self.betoltve.emit(len(self.lista))
            adat = self.friss("easylist.txt", EASYLIST_URL, lambda a: a.count("##") > 1000)
            hu = self.friss("hufilter.txt", HUFILTER_URL, lambda a: a.count("##") > 100)
            self.lista = self.lista | szuro.abp_tartomanyok(hu)
            if adat or hu:
                altalanos, self.oldal, self.kivetel = szuro.kozmetikus_beolvas(adat + "\n" + hu)
                self.css = szuro.kozmetikus_css(altalanos)
        except Exception:
            pass
        self.betoltve.emit(len(self.lista))

    def friss(self, nev, url, jo) -> str:
        f = CACHE / nev
        if not TOR and (not f.exists() or time.time() - f.stat().st_mtime > 7 * 86400):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "arnyek"})
                adat = urllib.request.urlopen(req, timeout=20).read().decode(errors="ignore")
                if jo(adat):
                    CACHE.mkdir(parents=True, exist_ok=True)
                    f.write_text(adat)
            except OSError:
                pass
        return f.read_text(errors="ignore") if f.exists() else ""


class TorIndito(QThread):
    allapot = Signal(int)

    def __init__(self):
        super().__init__()
        self.folyamat = None

    def run(self):
        if port_nyitva(TOR_PORT):
            self.allapot.emit(100)
            return
        adat = CACHE / "tor"
        adat.mkdir(parents=True, exist_ok=True, mode=0o700)
        torrc = CACHE / "torrc"
        torrc.touch()
        try:
            self.folyamat = subprocess.Popen(
                ["tor", "--defaults-torrc", str(torrc), "-f", str(torrc), "--SocksPort", str(TOR_PORT), "--DataDirectory", str(adat), "--Log", "notice stdout"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
        except FileNotFoundError:
            self.allapot.emit(-1)
            return
        utolso = 0
        for sor in self.folyamat.stdout:
            m = re.search(r"Bootstrapped (\d+)%", sor)
            if m:
                utolso = int(m.group(1))
                self.allapot.emit(utolso)
        if utolso < 100:
            self.allapot.emit(-2)


class Identitas:
    szamlalo = 0

    def __init__(self, ablak):
        Identitas.szamlalo += 1
        self.szin = IDENTITAS_SZINEK[(Identitas.szamlalo - 1) % len(IDENTITAS_SZINEK)]
        self.mag = secrets.token_hex(4)
        self.nev = self.mag[:4].upper()
        self.kivetelek: set[str] = set()
        self.lapok = 0
        self.profil = QWebEngineProfile(ablak)
        p = self.profil
        p.setHttpAcceptLanguage("hu-HU,hu;q=0.9,en;q=0.8")
        p.setHttpUserAgent(re.sub(r"\s*QtWebEngine/\S+", "", p.httpUserAgent()))
        p.setPersistentPermissionsPolicy(QWebEngineProfile.PersistentPermissionsPolicy.AskEveryTime)
        p.cookieStore().setCookieFilter(lambda k: not k.thirdParty)
        A = QWebEngineSettings.WebAttribute
        s = p.settings()
        for attr, ertek in [
            (A.PluginsEnabled, True), (A.PdfViewerEnabled, True), (A.FullScreenSupportEnabled, True),
            (A.ScreenCaptureEnabled, True), (A.DnsPrefetchEnabled, False), (A.HyperlinkAuditingEnabled, False),
            (A.WebRTCPublicInterfacesOnly, True), (A.LocalContentCanAccessRemoteUrls, False),
            (A.JavascriptCanOpenWindows, False), (A.PlaybackRequiresUserGesture, True),
        ]:
            s.setAttribute(attr, ertek)
        js = QWebEngineScript()
        js.setName("arnyek")
        js.setSourceCode((MAPPA / "ujjlenyomat.js").read_text().replace("__MAG__", self.mag))
        js.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        js.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        js.setRunsOnSubFrames(True)
        p.scripts().insert(js)
        p.downloadRequested.connect(ablak.letoltes)
        p.setNotificationPresenter(lambda n: subprocess.Popen(["notify-send", "-a", "Árnyék", "--", n.title(), n.message()]))
        self.kozmetika(ablak.blokk.css)

    def kozmetika(self, css: str):
        for regi in self.profil.scripts().find("arnyek-kozmetika"):
            self.profil.scripts().remove(regi)
        if not css:
            return
        js = QWebEngineScript()
        js.setName("arnyek-kozmetika")
        js.setSourceCode(
            f"(()=>{{if({json.dumps(sorted(ENGEDETT))}.includes(location.hostname))return;"
            + css_js(css) + "})()"
        )
        js.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        js.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        self.profil.scripts().insert(js)


class Elfogo(QWebEngineUrlRequestInterceptor):
    blokkolt = Signal(str)

    def __init__(self, lap):
        super().__init__(lap)
        self.kivetelek = lap.identitas.kivetelek
        self.lista = lap.ablak.blokk
        self.felhuzott: set[str] = set()

    def interceptRequest(self, info):
        url = info.requestUrl()
        if info.resourceType() == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame:
            s = url.toString()
            uj = szuro.tisztit(s) or szuro.https_ra(s, self.kivetelek)
            if uj:
                if uj.startswith("https://") and s.startswith("http://"):
                    self.felhuzott.add(url.host())
                info.redirect(QUrl(uj))
                return
        elif info.firstPartyUrl().host() not in ENGEDETT:
            d = szuro.tiltott(url.host(), self.lista.lista)
            if d:
                info.block(True)
                self.blokkolt.emit(d)
                return
        info.setHttpHeader(b"Sec-GPC", b"1")


class Oldal(QWebEnginePage):
    def __init__(self, lap):
        super().__init__(lap.identitas.profil, lap)
        self.lap = lap

    def createWindow(self, tipus):
        hatter = tipus == QWebEnginePage.WebWindowType.WebBrowserBackgroundTab
        return self.lap.ablak.uj_lap(self.lap.identitas, hatterben=hatter).page()


ENGEDELY_NEV = {
    "MediaAudioCapture": "mikrofon", "MediaVideoCapture": "kamera", "MediaAudioVideoCapture": "kamera és mikrofon",
    "Geolocation": "pontos helyzet", "Notifications": "értesítések", "DesktopVideoCapture": "képernyőmegosztás",
    "DesktopAudioVideoCapture": "képernyő és hang", "ClipboardReadWrite": "vágólap", "MouseLock": "egérzár",
    "LocalFontsAccess": "telepített betűtípusok",
}


class Lap(QWebEngineView):
    def __init__(self, ablak, identitas):
        super().__init__()
        self.ablak = ablak
        self.identitas = identitas
        identitas.lapok += 1
        self.blokkolva = Counter()
        self.setPage(Oldal(self))
        self.elfogo = Elfogo(self)
        self.elfogo.blokkolt.connect(self.blokk)
        self.page().setUrlRequestInterceptor(self.elfogo)
        pg = self.page()
        pg.permissionRequested.connect(self.engedely)
        pg.fullScreenRequested.connect(ablak.teljes_kepernyo)
        pg.desktopMediaRequested.connect(lambda r: r.selectScreen(r.screensModel().index(0, 0)))
        self.loadFinished.connect(self.betoltott)
        self.host = ""
        self.urlChanged.connect(self.uj_cim)
        pg.recentlyAudibleChanged.connect(lambda _: ablak.lap_frissult(self))
        pg.audioMutedChanged.connect(lambda _: ablak.lap_frissult(self))

    def uj_cim(self, u):
        if u.host() != self.host:
            self.host = u.host()
            self.blokkolva.clear()

    def blokk(self, d):
        self.blokkolva[d] += 1
        self.ablak.munkamenet[d] += 1
        self.ablak.lap_frissult(self)

    def betoltott(self, ok):
        u = self.url()
        if not ok and u.scheme() == "https" and u.host() in self.elfogo.felhuzott and u.host() not in self.identitas.kivetelek:
            self.identitas.kivetelek.add(u.host())
            u.setScheme("http")
            self.setUrl(u)
        sel = szuro.oldal_szelektorok(u.host(), self.ablak.blokk.oldal, self.ablak.blokk.kivetel) if ok and u.host() not in ENGEDETT else []
        if sel:
            self.page().runJavaScript(css_js(szuro.kozmetikus_css(sel)), QWebEngineScript.ScriptWorldId.ApplicationWorld)
        self.ablak.lap_frissult(self)

    def engedely(self, e: QWebEnginePermission):
        nev = ENGEDELY_NEV.get(e.permissionType().name, e.permissionType().name)
        v = QMessageBox.question(self.ablak, "Engedély", f"{e.origin().host()} ehhez kér hozzáférést: {nev}\n\nCsak erre az identitásra és csak most.")
        e.grant() if v == QMessageBox.Yes else e.deny()

    def uj_lap_oldal(self):
        self.setHtml(self.ablak.kezdolap(self.identitas), QUrl("about:blank"))


def cimke(szoveg: str) -> QLabel:
    c = QLabel(szoveg, objectName="cimke")
    c.setContentsMargins(8, 0, 8, 0)
    c.setIndent(0)
    return c


class LapSor(QWidget):
    def __init__(self, szin):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(8, 0, 8, 0)
        h.setSpacing(10)
        pont = QLabel()
        pont.setFixedSize(8, 8)
        pont.setStyleSheet(f"background:{szin};border-radius:4px;")
        self.cim = QLabel("Új lap")
        self.cim.setObjectName("lapcim")
        self.szam = QLabel("")
        self.szam.setObjectName("szam")
        h.addWidget(pont)
        h.addWidget(self.cim, 1)
        h.addWidget(self.szam)

    def beallit(self, cim, szam, hang=""):
        fm = self.cim.fontMetrics()
        self.cim.setText(fm.elidedText(cim or "Új lap", Qt.ElideRight, 160 if not hang else 120))
        self.szam.setText(" ".join(x for x in (hang, str(szam) if szam else "") if x))


class LapLista(QListWidget):
    kozepso = Signal(int)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MiddleButton:
            it = self.itemAt(e.position().toPoint())
            if it:
                self.kozepso.emit(self.row(it))
                return
        super().mouseReleaseEvent(e)


STILUS = f"""
* {{ font-family: Inter; font-size: 13px; color: {SZIN['szoveg']}; }}
QMainWindow, #jobb {{ background: {SZIN['hatter']}; }}
#oldalsav {{ background: {SZIN['mely']}; border-right: 1px solid {SZIN['vonal']}; }}
#marka {{ font-size: 15px; font-weight: 500; }}
#mod {{ font-family: 'JetBrains Mono'; font-size: 12px; color: {SZIN['halk']}; }}
#cimke {{ font-size: 12px; color: {SZIN['halk']}; }}
#allapotnev {{ color: {SZIN['masod']}; }}
#allapotertek, #szam {{ font-family: 'JetBrains Mono'; font-size: 12px; color: {SZIN['halk']}; }}
#lapcim {{ color: {SZIN['masod']}; }}
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ height: 36px; margin: 0 0 2px 0; border-radius: 8px; border: 1px solid transparent; }}
QListWidget::item:selected {{ background: {SZIN['emelt']}; border: 1px solid {SZIN['vonal']}; }}
QListWidget::item:hover:!selected {{ background: {SZIN['felulet']}; }}
#eszkozsor {{ background: {SZIN['hatter']}; border-bottom: 1px solid {SZIN['vonal']}; }}
QLineEdit {{ background: {SZIN['felulet']}; border: 1px solid {SZIN['vonal']}; border-radius: 8px; padding: 0 8px; selection-background-color: {SZIN['kijeloles']}; }}
QLineEdit:focus {{ background: {SZIN['emelt']}; border: 1px solid rgba(237,237,237,0.20); }}
QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 8px; }}
QToolButton:hover {{ background: {SZIN['emelt']}; }}
QToolButton:pressed {{ background: {SZIN['felulet']}; }}
QToolButton:focus {{ border: 1px solid rgba(237,237,237,0.20); }}
QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 8px; min-height: 32px; max-height: 32px; padding: 0 8px; text-align: left; color: {SZIN['masod']}; }}
QPushButton:hover {{ background: {SZIN['felulet']}; color: {SZIN['szoveg']}; }}
QPushButton:pressed {{ background: {SZIN['emelt']}; }}
QPushButton:focus {{ border: 1px solid rgba(237,237,237,0.20); }}
#pajzs {{ font-family: 'JetBrains Mono'; font-size: 12px; color: {SZIN['masod']}; padding: 0 8px; }}
QMenu {{ background: {SZIN['emelt']}; border: 1px solid {SZIN['vonal']}; border-radius: 12px; padding: 4px; }}
QMenu::item {{ padding: 8px 12px; border-radius: 8px; }}
QMenu::item:selected {{ background: rgba(237,237,237,0.06); }}
QMenu::item:disabled {{ color: {SZIN['halk']}; font-family: 'JetBrains Mono'; font-size: 12px; }}
QMenu::separator {{ height: 1px; background: {SZIN['vonal']}; margin: 4px 8px; }}
QProgressBar {{ background: transparent; border: none; max-height: 2px; }}
QProgressBar::chunk {{ background: {SZIN['lampa']}; }}
QMessageBox, QInputDialog, QFileDialog {{ background: {SZIN['felulet']}; }}
QToolTip {{ background: {SZIN['emelt']}; color: {SZIN['szoveg']}; border: 1px solid {SZIN['vonal']}; border-radius: 6px; padding: 4px 8px; }}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: {SZIN['emelt']}; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ background: none; height: 0; }}
"""


def paletta() -> QPalette:
    p = QPalette()
    for szerep, kulcs in [
        (QPalette.Window, "hatter"), (QPalette.Base, "felulet"), (QPalette.AlternateBase, "emelt"),
        (QPalette.Button, "emelt"), (QPalette.ToolTipBase, "emelt"),
        (QPalette.WindowText, "szoveg"), (QPalette.Text, "szoveg"), (QPalette.ButtonText, "szoveg"),
        (QPalette.ToolTipText, "szoveg"), (QPalette.PlaceholderText, "halk"), (QPalette.Highlight, "kijeloles"),
    ]:
        p.setColor(szerep, QColor(SZIN[kulcs]))
    p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    return p


class Ablak(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Árnyék")
        self.resize(1360, 860)
        self.munkamenet = Counter()
        self.blokk = Blokklista()
        self.kozmetika_kesz = False
        self.lapok: list[Lap] = []
        self.letoltesek: dict = {}

        gyoker = QWidget()
        fo = QHBoxLayout(gyoker)
        fo.setContentsMargins(0, 0, 0, 0)
        fo.setSpacing(0)

        self.oldalsav = QFrame(objectName="oldalsav")
        self.oldalsav.setFixedWidth(256)
        ov = QVBoxLayout(self.oldalsav)
        ov.setContentsMargins(12, 0, 12, 12)
        ov.setSpacing(0)
        fej = QFrame(objectName="fej")
        fej.setFixedHeight(48)
        fh = QHBoxLayout(fej)
        fh.setContentsMargins(8, 0, 8, 0)
        fh.addWidget(QLabel("Árnyék", objectName="marka"))
        fh.addStretch()
        self.mod = QLabel(objectName="mod")
        fh.addWidget(self.mod)
        ov.addWidget(fej)
        ov.addSpacing(12)
        ov.addWidget(cimke("Lapok"))
        ov.addSpacing(4)
        self.lista = LapLista()
        self.lista.currentRowChanged.connect(self.valt)
        self.lista.kozepso.connect(self.bezar)
        self.lista.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista.customContextMenuRequested.connect(self.lap_menu)
        ov.addWidget(self.lista, 1)
        ov.addSpacing(16)
        ov.addWidget(cimke("Állapot"))
        ov.addSpacing(4)
        racs = QGridLayout()
        racs.setContentsMargins(8, 0, 8, 0)
        racs.setHorizontalSpacing(12)
        racs.setVerticalSpacing(4)
        self.allapot: dict[str, QLabel] = {}
        for i, nev in enumerate(["Tiltólista", "DNS", "Identitás", "Letöltés"]):
            c = QLabel(nev, objectName="allapotnev")
            e = QLabel(objectName="allapotertek")
            e.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            racs.addWidget(c, i, 0)
            racs.addWidget(e, i, 1)
            self.allapot[nev] = e
            if nev == "Letöltés":
                self.letoltes_sor = (c, e)
                c.hide()
                e.hide()
        ov.addLayout(racs)
        ov.addSpacing(16)
        for szoveg, nev, fv in [
            ("Új identitás", "plusz", lambda: self.uj_lap()),
            ("Kiürítés", "radir", self.kiurit),
        ]:
            b = QPushButton(ikon(nev), szoveg)
            b.clicked.connect(fv)
            ov.addWidget(b)
        self.modvalto = QPushButton(ikon("halo"), "Kilépés a Torból" if TOR else "Tor mód")
        self.modvalto.clicked.connect(self.tor_valt)
        ov.addWidget(self.modvalto)

        jobb = QWidget(objectName="jobb")
        jv = QVBoxLayout(jobb)
        jv.setContentsMargins(0, 0, 0, 0)
        jv.setSpacing(0)
        self.eszkozsor = QFrame(objectName="eszkozsor")
        eh = QHBoxLayout(self.eszkozsor)
        self.eszkozsor.setFixedHeight(48)
        eh.setContentsMargins(12, 0, 12, 0)
        eh.setSpacing(4)
        for nev, fv in [("vissza", lambda: self.akt().back()), ("elore", lambda: self.akt().forward()), ("frissit", lambda: self.akt().reload())]:
            tb = QToolButton()
            tb.setIcon(ikon(nev, meret=16))
            tb.setIconSize(QSize(16, 16))
            tb.setFixedSize(32, 32)
            tb.clicked.connect(fv)
            eh.addWidget(tb)
        eh.addSpacing(8)
        self.cim = QLineEdit()
        self.cim.setPlaceholderText("Keresés vagy cím")
        self.cim.setFixedHeight(32)
        self.cim.returnPressed.connect(self.megnyit)
        self.lakat = QAction(ikon("lakat"), "", self.cim)
        self.cim.addAction(self.lakat, QLineEdit.LeadingPosition)
        eh.addWidget(self.cim, 1)
        eh.addSpacing(8)
        self.pajzs = QToolButton(objectName="pajzs")
        self.pajzs.setIcon(ikon("pajzs"))
        self.pajzs.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.pajzs.setFixedHeight(32)
        self.pajzs.clicked.connect(self.pajzs_menu)
        eh.addWidget(self.pajzs)
        jv.addWidget(self.eszkozsor)
        self.tolto = QProgressBar()
        self.tolto.setTextVisible(False)
        self.tolto.setFixedHeight(2)
        jv.addWidget(self.tolto)
        self.verem = QStackedWidget()
        jv.addWidget(self.verem, 1)

        fo.addWidget(self.oldalsav)
        fo.addWidget(jobb, 1)
        self.setCentralWidget(gyoker)

        for kulcs, fv in [
            ("Ctrl+T", lambda: self.uj_lap()),
            ("Ctrl+Shift+T", lambda: self.uj_lap(self.akt().identitas)),
            ("Ctrl+W", lambda: self.bezar(self.lista.currentRow())),
            ("Ctrl+L", lambda: (self.cim.setFocus(), self.cim.selectAll())),
            ("F6", lambda: (self.cim.setFocus(), self.cim.selectAll())),
            ("Ctrl+Tab", lambda: self.lista.setCurrentRow((self.lista.currentRow() + 1) % self.lista.count())),
            ("Ctrl+Shift+Tab", lambda: self.lista.setCurrentRow((self.lista.currentRow() - 1) % self.lista.count())),
            ("F5", lambda: self.akt().reload()), ("Ctrl+R", lambda: self.akt().reload()),
            ("Alt+Left", lambda: self.akt().back()), ("Alt+Right", lambda: self.akt().forward()),
            ("Ctrl+Shift+Del", self.kiurit), ("Ctrl+Shift+O", self.tor_valt),
            ("Ctrl+F", self.keres), ("Ctrl+Shift+R", self.olvaso), ("Ctrl+M", lambda: self.nemit(self.akt())), ("F12", self.fejleszto),
            ("Ctrl++", lambda: self.akt().setZoomFactor(self.akt().zoomFactor() + 0.1)),
            ("Ctrl+=", lambda: self.akt().setZoomFactor(self.akt().zoomFactor() + 0.1)),
            ("Ctrl+-", lambda: self.akt().setZoomFactor(max(0.3, self.akt().zoomFactor() - 0.1))),
            ("Ctrl+0", lambda: self.akt().setZoomFactor(1.0)),
            ("Ctrl+P", self.pdf),
            ("Escape", lambda: self.akt().page().triggerAction(QWebEnginePage.WebAction.ExitFullScreen) if self.isFullScreen() else None),
        ]:
            QShortcut(QKeySequence(kulcs), self, fv)

        self.blokk.betoltve.connect(lambda n: (self.info_frissit(), self.kozmetika()))
        self.blokk.start()
        self.tor = None
        self.tor_szazalek = 100
        if TOR:
            self.tor_szazalek = 0
            self.tor = TorIndito()
            self.tor.allapot.connect(self.tor_allapot)
            self.tor.start()
        self.info_frissit()
        self.uj_lap()
        for a in [x for x in ARGS if not x.startswith("--")]:
            self.uj_lap(url=szuro.cim_ertelmez(a, KERESO))

    def kozmetika(self):
        for idt in {lap.identitas for lap in self.lapok}:
            idt.kozmetika(self.blokk.css)
        if self.blokk.css and not self.kozmetika_kesz:
            self.kozmetika_kesz = True
            for lap in self.lapok:
                if lap.url().host() not in ENGEDETT:
                    lap.page().runJavaScript(css_js(self.blokk.css), QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def akt(self) -> Lap:
        return self.verem.currentWidget()

    def uj_lap(self, identitas=None, hatterben=False, url=None):
        lap = Lap(self, identitas or Identitas(self))
        lap.titleChanged.connect(lambda _: self.lap_frissult(lap))
        lap.urlChanged.connect(lambda _: self.lap_frissult(lap))
        lap.loadProgress.connect(lambda p: self.tolto.setValue(p if p < 100 else 0) if lap is self.akt() else None)
        self.lapok.append(lap)
        self.verem.addWidget(lap)
        it = QListWidgetItem()
        it.setSizeHint(QSize(0, 34))
        self.lista.addItem(it)
        self.lista.setItemWidget(it, LapSor(lap.identitas.szin))
        if url:
            lap.setUrl(QUrl(url))
        else:
            lap.uj_lap_oldal()
        if not hatterben:
            self.lista.setCurrentRow(self.lista.count() - 1)
            if not url:
                QTimer.singleShot(0, lambda: (self.cim.setFocus(), self.cim.clear()) if lap is self.akt() else None)
        self.lap_frissult(lap)
        return lap

    def bezar(self, i):
        if i < 0 or i >= len(self.lapok):
            return
        lap = self.lapok.pop(i)
        self.lista.takeItem(i)
        self.verem.removeWidget(lap)
        idt = lap.identitas
        idt.lapok -= 1
        lap.page().deleteLater()
        lap.deleteLater()
        if idt.lapok == 0:
            idt.profil.deleteLater()
        if not self.lapok:
            self.uj_lap()

    def valt(self, i):
        if 0 <= i < len(self.lapok):
            lap = self.lapok[i]
            self.verem.setCurrentWidget(lap)
            if lap.url().toString() in ("about:blank", ""):
                lap.uj_lap_oldal()
            self.cim.clearFocus()
            self.lap_frissult(lap)

    def lap_frissult(self, lap):
        if lap not in self.lapok:
            return
        i = self.lapok.index(lap)
        sor = self.lista.itemWidget(self.lista.item(i))
        ures = lap.url().toString() in ("about:blank", "")
        if sor:
            pg = lap.page()
            hang = "néma" if pg.isAudioMuted() else ("hang" if pg.recentlyAudible() else "")
            sor.beallit("Új lap" if ures else lap.title(), sum(lap.blokkolva.values()), hang)
        if lap is self.akt():
            if not self.cim.hasFocus():
                self.cim.setText("" if ures else lap.url().toString())
            titkos = lap.url().scheme() == "https" or ures
            self.lakat.setIcon(ikon("lakat") if titkos else ikon("nyitott", SZIN["lampa"]))
            self.lakat.setToolTip("Titkosított kapcsolat" if titkos else "Titkosítatlan kapcsolat, ezen a lapon minden lehallgatható")
            n = sum(lap.blokkolva.values())
            ki = lap.url().host() in ENGEDETT
            self.pajzs.setText("ki" if ki else str(n))
            self.pajzs.setIcon(ikon("pajzs", SZIN["lampa"] if ki else SZIN["masod"]))
            self.pajzs.setToolTip("Blokkolás és adatvédelem ezen az oldalon")
            self.setWindowTitle(("Árnyék" if ures else f"{lap.title()} · Árnyék"))

    def megnyit(self):
        s = self.cim.text().strip()
        if s:
            self.akt().setUrl(QUrl(szuro.cim_ertelmez(s, KERESO)))
            self.akt().setFocus()

    def info_frissit(self):
        if TOR:
            self.mod.setText("tor" if self.tor_szazalek >= 100 else f"tor {self.tor_szazalek}%")
            dns = "Tor-láncon"
        else:
            self.mod.setText("közvetlen")
            dns = "rendszer" if RENDSZER_DNS else "titkosított"
        self.allapot["Tiltólista"].setText(f"{len(self.blokk.lista):,}".replace(",", " "))
        self.allapot["DNS"].setText(dns)
        self.allapot["Identitás"].setText(f"{len({id(l.identitas) for l in self.lapok})} ({len(self.lapok)} lap)")

    def tor_allapot(self, sz):
        if sz < 0:
            QMessageBox.warning(self, "Tor", "A tor nincs telepítve. Telepítés: sudo pacman -S tor" if sz == -1 else "A tor leállt, mielőtt kapcsolódott volna. Most semmi nem megy ki a hálózatra.")
            sz = 0
        self.tor_szazalek = sz
        self.info_frissit()

    def tor_valt(self):
        if QMessageBox.question(self, "Mód váltása", "A váltás minden lapot és identitást töröl. Mehet?") != QMessageBox.Yes:
            return
        uj = [a for a in ARGS if a != "--tor"] + ([] if TOR else ["--tor"])
        self.leallit()
        os.execv(sys.executable, [sys.executable, str(MAPPA / "arnyek.py")] + uj)

    def kiurit(self):
        for _ in range(len(self.lapok)):
            lap = self.lapok.pop()
            self.lista.takeItem(len(self.lapok))
            self.verem.removeWidget(lap)
            lap.identitas.lapok -= 1
            lap.page().deleteLater()
            lap.deleteLater()
            if lap.identitas.lapok == 0:
                lap.identitas.profil.deleteLater()
        self.munkamenet.clear()
        QGuiApplication.clipboard().clear()
        Identitas.szamlalo = 0
        self.uj_lap()
        self.info_frissit()

    def pajzs_menu(self):
        lap = self.akt()
        host = lap.url().host()
        m = QMenu(self)
        if lap.blokkolva:
            for d, c in lap.blokkolva.most_common(8):
                m.addAction(f"{d}   {c}").setEnabled(False)
        else:
            m.addAction("Ezen az oldalon nem volt mit blokkolni").setEnabled(False)
        m.addSeparator()
        if host:
            a = m.addAction(f"Blokkolás itt: {host}")
            a.setCheckable(True)
            a.setChecked(host not in ENGEDETT)
            a.toggled.connect(lambda be: (ENGEDETT.discard(host) if be else ENGEDETT.add(host), self.kozmetika(), lap.reload()))
        s = lap.identitas.profil.settings()
        A = QWebEngineSettings.WebAttribute
        js = m.addAction("JavaScript ebben az identitásban")
        js.setCheckable(True)
        js.setChecked(s.testAttribute(A.JavascriptEnabled))
        js.toggled.connect(lambda be: (s.setAttribute(A.JavascriptEnabled, be), lap.reload()))
        m.addSeparator()
        m.addAction("Sütik és gyorsítótár törlése ebben az identitásban", lambda: (
            lap.identitas.profil.cookieStore().deleteAllCookies(), lap.identitas.profil.clearHttpCache(), lap.reload()))
        m.addAction("Megnyitás új identitásban", lambda: self.uj_lap(url=lap.url().toString()))
        m.exec(self.pajzs.mapToGlobal(self.pajzs.rect().bottomLeft()))

    def nemit(self, lap):
        lap.page().setAudioMuted(not lap.page().isAudioMuted())

    def lap_menu(self, pont):
        it = self.lista.itemAt(pont)
        if not it:
            return
        i = self.lista.row(it)
        lap = self.lapok[i]
        m = QMenu(self)
        m.addAction("Hang vissza" if lap.page().isAudioMuted() else "Némítás", lambda: self.nemit(lap))
        m.addAction("Újra új identitásban", lambda: self.uj_lap(url=lap.url().toString()))
        m.addAction("Lap ugyanebben az identitásban", lambda: self.uj_lap(lap.identitas))
        m.addSeparator()
        m.addAction("Bezárás", lambda: self.bezar(self.lapok.index(lap)))
        m.addAction("Többi bezárása", lambda: [self.bezar(self.lapok.index(x)) for x in list(self.lapok) if x is not lap])
        m.exec(self.lista.viewport().mapToGlobal(pont))

    def olvaso(self):
        self.akt().page().runJavaScript((MAPPA / "olvaso.js").read_text(), QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def pdf(self):
        ut, _ = QFileDialog.getSaveFileName(self, "Mentés PDF-be", str(Path.home() / "lap.pdf"))
        if ut:
            self.akt().printToPdf(ut)

    def keres(self):
        s, ok = QInputDialog.getText(self, "Keresés az oldalon", "Szöveg")
        self.akt().findText(s if ok else "")

    def fejleszto(self):
        v = QWebEngineView()
        v.setPage(QWebEnginePage(self.akt().identitas.profil, v))
        self.akt().page().setDevToolsPage(v.page())
        v.setWindowTitle("Fejlesztői eszközök")
        v.resize(1000, 700)
        v.setAttribute(Qt.WA_DeleteOnClose)
        v.show()

    def teljes_kepernyo(self, kerdes):
        kerdes.accept()
        be = kerdes.toggleOn()
        self.oldalsav.setVisible(not be)
        self.eszkozsor.setVisible(not be)
        self.tolto.setVisible(not be)
        self.showFullScreen() if be else self.showNormal()

    def letoltes(self, d: QWebEngineDownloadRequest):
        alap = Path.home() / "Letöltések"
        if not alap.exists():
            alap = Path.home() / "Downloads"
        ut, _ = QFileDialog.getSaveFileName(self, "Letöltés mentése", str(alap / d.downloadFileName()))
        if not ut:
            d.cancel()
            return
        d.setDownloadDirectory(str(Path(ut).parent))
        d.setDownloadFileName(Path(ut).name)
        for w in self.letoltes_sor:
            w.show()
        self.allapot["Letöltés"].setToolTip(d.downloadFileName())
        d.receivedBytesChanged.connect(lambda: self.allapot["Letöltés"].setText(f"{d.receivedBytes() * 100 // max(d.totalBytes(), 1)}%"))
        d.isFinishedChanged.connect(lambda: ([w.hide() for w in self.letoltes_sor], subprocess.Popen(["notify-send", "-a", "Árnyék", "--", "Letöltve", d.downloadFileName()])))
        d.accept()

    def kezdolap(self, idt: Identitas) -> str:
        osszes = sum(self.munkamenet.values())
        top = self.munkamenet.most_common(5)
        maxi = top[0][1] if top else 1
        sorok = "".join(
            f'<li><span class="d">{html.escape(d)}</span><span class="n">{n}</span>'
            f'<i><b style="width:{max(2, n * 100 // maxi)}%;{"background:" + SZIN["lampa"] if j == 0 else ""}"></b></i></li>'
            for j, (d, n) in enumerate(top)
        ) or '<li class="ures">Ebben a munkamenetben még semmi nem próbált követni</li>'
        if TOR:
            halo = "Tor-hálózat, három ugrás"
        elif RENDSZER_DNS:
            halo = "Közvetlen, a rendszer DNS-ével"
        else:
            halo = "Közvetlen, titkosított DNS: " + html.escape(urlsplit(DOH).hostname or DOH)
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
<dt>Sütik</dt><dd>Csak ez az identitás látja őket</dd>
<dt>Ujjlenyomat</dt><dd>Vászon és hang zajosítva, ez a mintája</dd>
<dt>Hálózat</dt><dd>{halo}</dd>
<dt>WebRTC</dt><dd>{"Kikapcsolva, csak Toron át mehetne" if TOR else "Helyi cím rejtve, a hívás működik"}</dd>
<dt>Lemez</dt><dd>Nincs előzmény, nincs gyorsítótár</dd>
</dl></div>
</div>
<div class="blokk"><div><div class="szam">{osszes}</div><div class="al">blokkolt kérés ebben a munkamenetben, {len(self.munkamenet)} követőtől</div></div>
<ul>{sorok}</ul></div>
<footer><span><kbd>Ctrl</kbd><kbd>T</kbd> új identitás</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>T</kbd> lap ugyanebben</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>Del</kbd> kiürítés</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>R</kbd> olvasó</span><span><kbd>Ctrl</kbd><kbd>Shift</kbd><kbd>O</kbd> Tor</span></footer>
</main></body></html>"""

    def leallit(self):
        if self.tor and self.tor.folyamat:
            self.tor.folyamat.terminate()

    def closeEvent(self, e):
        self.leallit()
        for lap in self.lapok:
            lap.page().deleteLater()
        super().closeEvent(e)


def main():
    if not TOR and not RENDSZER_DNS:
        m = QWebEngineGlobalSettings.DnsMode()
        m.secureMode = QWebEngineGlobalSettings.SecureDnsMode.SecureOnly
        m.serverTemplates = [DOH]
        QWebEngineGlobalSettings.setDnsMode(m)
    app = QApplication([sys.argv[0], "--webEngineArgs"] + chromium_flagek())
    app.setApplicationName("Árnyék")
    app.setDesktopFileName("arnyek")
    app.setStyle("Fusion")
    app.setPalette(paletta())
    app.setStyleSheet(STILUS)
    ablak = Ablak()
    ablak.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
