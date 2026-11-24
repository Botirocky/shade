#!/usr/bin/env bash
set -euo pipefail

MAPPA="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BIN="$HOME/.local/bin"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
IKONOK="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

if [[ "${1:-}" == "--eltavolit" ]]; then
    rm -f "$BIN/arnyek" "$APPS/arnyek.desktop" "$IKONOK/arnyek.svg"
    update-desktop-database "$APPS" 2>/dev/null || true
    echo "Az Árnyék eltávolítva. A könyvjelzők megmaradtak: ${XDG_DATA_HOME:-$HOME/.local/share}/arnyek"
    exit 0
fi

hiany=()
python3 -c "import PySide6.QtWebEngineWidgets" 2>/dev/null || hiany+=(pyside6 qt6-webengine)
python3 -c "import cryptography" 2>/dev/null || hiany+=(python-cryptography)
command -v tor >/dev/null || hiany+=(tor)
command -v aplay >/dev/null || hiany+=(alsa-utils)
if ((${#hiany[@]})); then
    if command -v pacman >/dev/null; then
        echo "Hiányzó csomagok: ${hiany[*]}"
        sudo pacman -S --needed "${hiany[@]}"
    else
        echo "Telepítsd ezeket a csomagkezelőddel: ${hiany[*]}" >&2
        exit 1
    fi
fi

mkdir -p "$BIN" "$APPS" "$IKONOK"
cat > "$BIN/arnyek" <<EOF
#!/bin/sh
exec python3 "$MAPPA/arnyek.py" "\$@"
EOF
chmod 755 "$BIN/arnyek"
install -m 644 "$MAPPA/arnyek.svg" "$IKONOK/arnyek.svg"

cat > "$APPS/arnyek.desktop" <<EOF
[Desktop Entry]
Name=Árnyék
GenericName=Privát böngésző
Comment=Lapokra bontott, eldobható identitások, Tor mód
Exec=$BIN/arnyek %U
Icon=arnyek
Type=Application
Terminal=false
StartupWMClass=arnyek
Categories=Network;WebBrowser;
MimeType=text/html;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
Keywords=web;böngésző;privát;tor;
Actions=tor;rendszerdns;

[Desktop Action tor]
Name=Árnyék Tor módban
Exec=$BIN/arnyek --tor

[Desktop Action rendszerdns]
Name=Árnyék rendszer-DNS-sel
Exec=$BIN/arnyek --rendszer-dns
EOF
update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache -q "${IKONOK%/scalable/apps}" 2>/dev/null || true

case ":$PATH:" in *":$BIN:"*) ;; *) echo "Figyelem: $BIN nincs a PATH-ban" ;; esac
echo "Az Árnyék telepítve: $BIN/arnyek és az alkalmazásmenü."
echo "Alapértelmezett böngészőnek: xdg-settings set default-web-browser arnyek.desktop"
