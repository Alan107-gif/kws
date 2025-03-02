#!/bin/bash
# Erstelle im Home-Verzeichnis einen Ordner namens "kws"
KWS_DIR="$HOME/kws"
if [ ! -d "$KWS_DIR" ]; then
    mkdir -p "$KWS_DIR"
    echo "Ordner $KWS_DIR wurde erstellt."
else
    echo "Ordner $KWS_DIR existiert bereits."
fi

# URL zum ZIP-Paket (bitte anpassen!)
ZIP_URL="http://a38.corecosmetic.de/wp-content/uploads/2025/03/kws-py.zip"
ZIP_FILE="$KWS_DIR/kws_package.zip"

# Lade das ZIP-Paket herunter
echo "Lade ZIP-Paket herunter..."
curl -L -o "$ZIP_FILE" "$ZIP_URL"

# Entpacke das ZIP-Paket in den kws-Ordner
echo "Entpacke das ZIP-Paket..."
unzip -o "$ZIP_FILE" -d "$KWS_DIR"

# Entferne das ZIP-Paket nach dem Entpacken
rm "$ZIP_FILE"
echo "ZIP-Paket wurde entpackt und entfernt."

# Autostart-Eintrag erstellen (für GNOME, KDE & Co.)
AUTOSTART_DIR="$HOME/.config/autostart"
if [ ! -d "$AUTOSTART_DIR" ]; then
    mkdir -p "$AUTOSTART_DIR"
fi

DESKTOP_FILE="$AUTOSTART_DIR/kws-server.desktop"
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Type=Application
Exec=python3 $KWS_DIR/kws.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=kws-server
Comment=Startet den kws-server automatisch
EOL

echo "Autostart-Eintrag wurde unter $DESKTOP_FILE erstellt."
echo "Installation abgeschlossen. Beim nächsten Login startet der kws-server automatisch."
