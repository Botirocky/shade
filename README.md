# Árnyék

Privát asztali böngésző Chromium-motorral (PySide6 + Qt WebEngine).

- Minden lap külön, memóriában élő identitás: saját sütik, saját ujjlenyomat-mag, bezáráskor eltűnik
- Követő- és reklámblokkolás (StevenBlack hosts, hetente frissül, `~/.cache/arnyek/hosts.txt`)
- Kozmetikus reklámszűrés: EasyList + hufilter (magyar oldalak) `##` szabályai, `#@#` kivételekkel (`~/.cache/arnyek/`, hetente frissül)
- DRM (Netflix stb.): a Widevine-t első induláskor `~/.local/share/arnyek/WidevineCdm`-be másolja Chrome/Chromium/Playwright mellől
- Követő URL-paraméterek levágása (utm_*, fbclid, gclid…), http → https emelés visszaeséssel
- Harmadik féltől jövő sütik tiltva, `Sec-GPC: 1`
- Vászon-, hang- és WebGL-ujjlenyomat zajosítva identitásonként
- Titkosított DNS (Mullvad DoH); a `*.park.lan` és `*.nagy.park.lan` indításkor a rendszer-DNS-ből kerül feloldásra (`ARNYEK_HELYI`)
- WebRTC: a helyi cím rejtve, hívás működik; Tor módban teljesen ki
- Tor mód: saját tor-folyamatot indít (9350), ha nincs futó; időzóna UTC; ellenőrizve: check.torproject.org → IsTor true
- Pajzs-menü: blokkolt tartományok, blokkolás ki ezen az oldalon, JavaScript ki/be identitásonként, sütik törlése
- Olvasó mód (Ctrl Shift R), lap-menü (jobb klikk): némítás, újranyitás új identitásban, többi bezárása
- Videó, PDF, teljes képernyő, letöltés, kamera/mikrofon engedélykéréssel, képernyőmegosztás, fejlesztői eszközök

## Indítás

    python arnyek.py [cím…] [--tor] [--rendszer-dns]

`--rendszer-dns`: a rendszer DNS-ét használja (pl. `*.park.lan` címekhez).
`ARNYEK_KERESO`, `ARNYEK_DOH` környezeti változóval a kereső és a DoH-szerver állítható.

## Billentyűk

| | |
|---|---|
| Ctrl T | új lap új identitással |
| Ctrl Shift T | új lap ugyanebben az identitásban |
| Ctrl W / középső klikk | lap bezárása |
| Ctrl Shift Del | kiürítés: minden lap, identitás és a vágólap törlése |
| Ctrl Shift O | Tor mód be/ki (újraindul) |
| Ctrl Shift R | olvasó mód |
| Ctrl M | némítás |
| Ctrl L, Ctrl F, Ctrl P, F12 | cím, keresés, PDF, fejlesztői eszközök |

Teszt: `python szuro.py`
