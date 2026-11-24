# Árnyék

Privát asztali böngésző Chromium-motorral (PySide6 + Qt WebEngine).

- Minden lap külön, memóriában élő identitás: saját sütik, saját ujjlenyomat-mag, bezáráskor eltűnik
- Követő- és reklámblokkolás (StevenBlack hosts, hetente frissül, `~/.cache/arnyek/hosts.txt`)
- Követő URL-paraméterek levágása (utm_*, fbclid, gclid…), http → https emelés visszaeséssel
- Harmadik féltől jövő sütik tiltva, `Sec-GPC: 1`
- Vászon-, hang- és WebGL-ujjlenyomat zajosítva identitásonként
- Titkosított DNS (Mullvad DoH), WebRTC nem árulja el a helyi címet
- Tor mód: saját tor-folyamatot indít, ha nincs futó
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
| Ctrl L, Ctrl F, Ctrl P, F12 | cím, keresés, PDF, fejlesztői eszközök |

Teszt: `python szuro.py`
