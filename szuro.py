import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

KOVETO_PARAM = re.compile(
    r"^(utm_\w+|fbclid|gclid|dclid|gbraid|wbraid|msclkid|mc_eid|mc_cid|igshid|yclid|"
    r"_hsenc|_hsmi|mkt_tok|ref_src|twclid|ttclid|li_fat_id|oly_anon_id|oly_enc_id|vero_id|_openstat)$",
    re.I,
)
HELYI = re.compile(
    r"(^localhost$|\.localhost$|\.lan$|\.local$|\.internal$|\.onion$|\.home\.arpa$|"
    r"^127\.|^10\.|^192\.168\.|^172\.(1[6-9]|2\d|3[01])\.|^100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.|^\[|^[\d.]+$)"
)

ALAP_TILTOTT = {
    "doubleclick.net", "google-analytics.com", "googletagmanager.com", "googlesyndication.com",
    "googleadservices.com", "adservice.google.com", "connect.facebook.net", "analytics.tiktok.com",
    "hotjar.com", "mixpanel.com", "segment.io", "segment.com", "scorecardresearch.com", "quantserve.com",
    "criteo.com", "criteo.net", "taboola.com", "outbrain.com", "adnxs.com", "amazon-adsystem.com",
    "clarity.ms", "bat.bing.com", "ads.linkedin.com", "px.ads.linkedin.com", "static.ads-twitter.com",
    "fullstory.com", "newrelic.com", "nr-data.net", "sentry-cdn.com", "branch.io", "app-measurement.com",
    "gemius.pl", "hit.gemius.pl", "adform.net", "rubiconproject.com", "pubmatic.com", "openx.net",
}


def tisztit(url: str) -> str | None:
    r = urlsplit(url)
    if not r.query:
        return None
    marad = [(k, v) for k, v in parse_qsl(r.query, keep_blank_values=True) if not KOVETO_PARAM.match(k)]
    if len(marad) == len(parse_qsl(r.query, keep_blank_values=True)):
        return None
    return urlunsplit((r.scheme, r.netloc, r.path, urlencode(marad), r.fragment))


def helyi(host: str) -> bool:
    return bool(HELYI.search(host.lower()))


def https_ra(url: str, kivetelek: set[str]) -> str | None:
    r = urlsplit(url)
    if r.scheme != "http" or not r.hostname or helyi(r.hostname) or r.hostname in kivetelek:
        return None
    return urlunsplit(("https", r.netloc, r.path, r.query, r.fragment))


def tiltott(host: str, lista: set[str]) -> str | None:
    resz = host.lower().rstrip(".").split(".")
    for i in range(len(resz) - 1):
        d = ".".join(resz[i:])
        if d in lista:
            return d
    return None


def hosts_beolvas(szoveg: str) -> set[str]:
    ki = set()
    for sor in szoveg.splitlines():
        sor = sor.split("#", 1)[0].split()
        if len(sor) >= 2 and sor[0] in ("0.0.0.0", "127.0.0.1") and sor[1] not in ("localhost", "0.0.0.0"):
            ki.add(sor[1].lower())
        elif len(sor) == 1 and "." in sor[0]:
            ki.add(sor[0].lower())
    return ki


def kozmetikus_beolvas(szoveg: str) -> tuple[list[str], dict[str, list[str]], dict[str, set[str]]]:
    altalanos, oldal, kivetel = [], {}, {}
    for sor in szoveg.splitlines():
        if sor.startswith(("!", "[")) or "#" not in sor:
            continue
        if "#@#" in sor:
            domainek, sel = sor.split("#@#", 1)
            if domainek and not re.search(r"[~{]|^\+js", sel + domainek):
                kivetel.setdefault(sel, set()).update(d.lower() for d in domainek.split(","))
            continue
        if "##" not in sor or re.search(r"#[?$%]#|##\+js", sor):
            continue
        domainek, sel = sor.split("##", 1)
        if not sel or "{" in sel:
            continue
        if not domainek:
            altalanos.append(sel)
        elif "~" not in domainek:
            for d in domainek.split(","):
                oldal.setdefault(d.lower(), []).append(sel)
    oldal["*"] = [x for x in altalanos if x in kivetel]
    return [x for x in altalanos if x not in kivetel], oldal, kivetel


def abp_tartomanyok(szoveg: str) -> set[str]:
    return {m.group(1).lower() for m in re.finditer(r"(?m)^\|\|([a-z0-9.-]+\.[a-z]{2,})\^$", szoveg)}


def _illik(host: str, domainek) -> bool:
    return any(host == d or host.endswith("." + d) for d in domainek)


def kozmetikus_css(szelektorok: list[str]) -> str:
    return "".join(f"{s}{{display:none!important}}\n" for s in szelektorok)


def oldal_szelektorok(host: str, oldal: dict[str, list[str]], kivetel: dict[str, set[str]] | None = None) -> list[str]:
    host = host.lower()
    reszek = host.split(".")
    jeloltek = oldal.get("*", []) + [s for i in range(len(reszek) - 1) for s in oldal.get(".".join(reszek[i:]), [])]
    return [s for s in jeloltek if not _illik(host, (kivetel or {}).get(s, ()))]


KULCSSZAVAK = {
    "w": "https://hu.wikipedia.org/w/index.php?search={}",
    "wen": "https://en.wikipedia.org/w/index.php?search={}",
    "yt": "https://www.youtube.com/results?search_query={}",
    "gh": "https://github.com/search?q={}",
    "osm": "https://www.openstreetmap.org/search?query={}",
    "arch": "https://wiki.archlinux.org/index.php?search={}",
    "aur": "https://aur.archlinux.org/packages?K={}",
    "mdn": "https://developer.mozilla.org/search?q={}",
    "pypi": "https://pypi.org/search/?q={}",
    "sp": "https://www.startpage.com/do/search?query={}",
    "ddg": "https://duckduckgo.com/?q={}",
}


def cim_ertelmez(szoveg: str, kereso: str) -> str:
    s = szoveg.strip()
    kulcs, _, maradek = s.partition(" ")
    if kulcs.lower() in KULCSSZAVAK and maradek.strip():
        from urllib.parse import quote_plus
        return KULCSSZAVAK[kulcs.lower()].format(quote_plus(maradek.strip()))
    if re.match(r"^[a-z][a-z0-9+.-]*://", s, re.I) or s.startswith(("about:", "view-source:", "data:")):
        return s
    if " " not in s and (re.match(r"^[\w.-]+\.[a-z]{2,}(:\d+)?(/.*)?$", s, re.I) or re.match(r"^(localhost|[\d.]+)(:\d+)?(/.*)?$", s)):
        host = re.split(r"[:/]", s, maxsplit=1)[0]
        return ("http://" if helyi(host) else "https://") + s
    from urllib.parse import quote_plus
    return kereso.format(quote_plus(s))


if __name__ == "__main__":
    assert tisztit("https://a.hu/x?utm_source=fb&id=3&fbclid=z") == "https://a.hu/x?id=3"
    assert tisztit("https://a.hu/x?id=3") is None
    assert https_ra("http://index.hu/a?b=1", set()) == "https://index.hu/a?b=1"
    assert https_ra("http://192.168.1.185/", set()) is None
    assert https_ra("http://kozpont.park.lan/", set()) is None
    assert https_ra("http://regi.hu/", {"regi.hu"}) is None
    assert tiltott("www.google-analytics.com", ALAP_TILTOTT) == "google-analytics.com"
    assert tiltott("google.com", ALAP_TILTOTT) is None
    assert hosts_beolvas("0.0.0.0 ads.x.com\n127.0.0.1 localhost\n# k\nfoo.net") == {"ads.x.com", "foo.net"}
    k = "https://duckduckgo.com/?q={}"
    assert cim_ertelmez("index.hu", k) == "https://index.hu"
    assert cim_ertelmez("picloud.park.lan:8094", k) == "http://picloud.park.lan:8094"
    assert cim_ertelmez("mi az a tor", k) == "https://duckduckgo.com/?q=mi+az+a+tor"
    assert cim_ertelmez("localhost:3000", k) == "http://localhost:3000"
    assert cim_ertelmez("w Budapest ostroma", k) == "https://hu.wikipedia.org/w/index.php?search=Budapest+ostroma"
    assert cim_ertelmez("yt", k) == "https://duckduckgo.com/?q=yt"
    assert cim_ertelmez("wikipedia.org", k) == "https://wikipedia.org"
    a, o, k = kozmetikus_beolvas("! x\n##.ad\nindex.hu,telex.hu##.banner\n~x.hu##.no\nfoo.com#@#.ad\nbar.com#?#div:has-text(x)\n##+js(x)\n###top-ad")
    assert a == ["#top-ad"], a
    assert o == {"index.hu": [".banner"], "telex.hu": [".banner"], "*": [".ad"]}, o
    assert k == {".ad": {"foo.com"}}, k
    assert oldal_szelektorok("www.index.hu", o, k) == [".ad", ".banner"]
    assert oldal_szelektorok("www.foo.com", o, k) == []
    assert oldal_szelektorok("hu", o, k) == [".ad"]
    assert abp_tartomanyok("||ads.hu^\n||x.hu^$third-party\n||*$image\n") == {"ads.hu"}
    assert kozmetikus_css([".ad"]) == ".ad{display:none!important}\n"
    print("szuro: minden teszt ok")
