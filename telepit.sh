#!/usr/bin/env bash
set -euo pipefail

MAPPA="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BIN="$HOME/.local/bin"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
IKONOK="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

if [[ "${1:-}" == "--eltavolit" ]]; then
    rm -f "$BIN/shade" "$APPS/shade.desktop" "$IKONOK/shade.svg"
    update-desktop-database "$APPS" 2>/dev/null || true
    echo "A Shade eltávolítva. A könyvjelzők megmaradtak: ${XDG_DATA_HOME:-$HOME/.local/share}/shade"
    exit 0
fi

hiany=()
python3 -c "import gi; gi.require_version('WebKit', '6.0'); gi.require_version('Gtk', '4.0')" 2>/dev/null || hiany+=(webkitgtk-6.0 gtk4 python-gobject)
command -v cc >/dev/null || hiany+=(gcc)
command -v pkg-config >/dev/null || hiany+=(pkgconf)
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
rm -f "$BIN/arnyek" "$APPS/arnyek.desktop" "$IKONOK/arnyek.svg"
cat > "$BIN/shade" <<EOF
#!/bin/sh
exec python3 "$MAPPA/shade.py" "\$@"
EOF
chmod 755 "$BIN/shade"
install -m 644 "$MAPPA/shade.svg" "$IKONOK/shade.svg"

cat > "$APPS/shade.desktop" <<EOF
[Desktop Entry]
Name=Shade
GenericName=Privát böngésző
Comment=Lapokra bontott, eldobható identitások, Tor mód
Exec=$BIN/shade %U
Icon=shade
Type=Application
Terminal=false
StartupWMClass=shade
Categories=Network;WebBrowser;
MimeType=text/html;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
Keywords=web;böngésző;privát;tor;
Actions=tor;

[Desktop Action tor]
Name=Shade Tor módban
Exec=$BIN/shade --tor
EOF
update-desktop-database "$APPS" 2>/dev/null || true
gtk-update-icon-cache -q "${IKONOK%/scalable/apps}" 2>/dev/null || true

case ":$PATH:" in *":$BIN:"*) ;; *) echo "Figyelem: $BIN nincs a PATH-ban" ;; esac
echo "A Shade telepítve: $BIN/shade és az alkalmazásmenü."
echo "Alapértelmezett böngészőnek: xdg-settings set default-web-browser shade.desktop"
