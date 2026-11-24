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
- Olvasó mód (Ctrl Shift R), lap-menü (jobb klikk): némítás, duplikálás, újranyitás új identitásban, többi bezárása
- Titkosított könyvjelzők: jelszóból scrypt-kulcs, AES-GCM, `~/.local/share/arnyek/konyvjelzok.bin` (0600); jelszó nélkül a fájlból semmi nem olvasható ki
- Címsor-kiegészítés a könyvjelzőkből és a nyitott lapokból
- Alvó lapok: a 10 percig háttérben álló, néma lap lefagy, kattintásra felébred
- Kulcsszavas keresés a címsorban: `w` (magyar Wikipédia), `wen`, `yt`, `gh`, `osm`, `arch`, `aur`, `mdn`, `pypi`, `sp` (Startpage), `ddg`, pl. `w Budapest ostroma`
- Biztonsági szint a pajzs-menüben (Tor Browser mintára): Normál, Szigorúbb (WebGL ki, titkosítatlan http-n JavaScript ki), Legszigorúbb (JavaScript és WebGL mindenhol ki)
- Sötét mód kényszerítése minden oldalra (pajzs-menü vagy Ctrl K)
- Felolvasás: a Piper és a hang helye `ARNYEK_PIPER` és `ARNYEK_HANG` változóval állítható; semmi nem megy ki a gépről
- Letöltések gomb az eszközsoron (a munkamenet letöltései, megnyitás, mappa)
- Videó, PDF, teljes képernyő, letöltés, kamera/mikrofon engedélykéréssel, képernyőmegosztás, fejlesztői eszközök

## Indítás

    python arnyek.py [cím…] [--tor] [--rendszer-dns]

`--rendszer-dns`: a rendszer DNS-ét használja (pl. `*.park.lan` címekhez).
`ARNYEK_KERESO`, `ARNYEK_DOH` környezeti változóval a kereső és a DoH-szerver állítható.

## Billentyűk

| | |
|---|---|
| Ctrl T | új lap új identitással |
| Ctrl Shift N | új lap ugyanebben az identitásban |
| Ctrl Shift T | bezárt lap visszanyitása |
| Ctrl D | könyvjelző be/ki (csillag a címsorban) |
| Ctrl K | parancssor: lapok, könyvjelzők, parancsok egy helyen |
| Ctrl \\ | osztott nézet be/ki (két lap egymás mellett; lap-menü: „Megnyitás osztott nézetben”) |
| Ctrl U | oldal forrása |
| Ctrl Shift C | link másolása |
| Ctrl Shift S | képernyőkép a látható részről |
| Ctrl + / − / 0 | nagyítás, oldalanként megjegyezve (csak memóriában) |
| Ctrl W / középső klikk | lap bezárása |
| Ctrl Shift Del | kiürítés: minden lap, identitás, bezárt lap, nagyítás és a vágólap törlése, könyvjelzők lezárása |
| Ctrl Shift O | Tor mód be/ki (újraindul) |
| Ctrl Shift R | olvasó mód |
| Ctrl M | némítás |
| Ctrl F | keresősáv az oldalon (Enter / Shift+Enter: következő / előző, Esc: bezár) |
| Ctrl Shift U | felolvasás helyi Piper-hanggal (kijelölés, vagy a cikk szövege), újra: leállít |
| Ctrl Shift L | Tor módban: új Tor-útvonal és az oldal újranyitása új identitásban |
| Ctrl L, Ctrl P, F12 | cím, PDF, fejlesztői eszközök |

Teszt: `python szuro.py`
