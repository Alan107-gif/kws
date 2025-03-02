# kws
Kontakt-work-Station is a decentralized communication network like mobile towers.

KWS - Kommunikationsnetzwerk    -OpenScource!

Beschreibung: KWS ist eine leichte, in Python implementierte Lösung für ein dezentrales Kommunikationsnetz. Das System stellt eine direkte, computer-zu-computer Verbindung her – ähnlich einem Mesh-Netzwerk. Es besteht aus drei Hauptkomponenten: • kws.py – der Server, der dauerhaft läuft, einen einzigartigen Auth-Key generiert und Konfigurations- sowie Kontaktdateien (contaktd.cdf) verwaltet. • kws-client.py – der Client, der periodisch Anfragen (z. B. INFO) an alle Kontakte sendet und fehlgeschlagene Nachrichten in einer Datei (data.ksys) zwischenspeichert. • kws-service.py – eine Befehlszeilenschnittstelle, über die der Nutzer Kontakte hinzufügen, Nachrichten senden und Anfragen (z. B. ADDLIST, LIST) manuell auslösen kann.

Vorteile: • Leichtgewichtig: Es werden nur systemeigene Bibliotheken (Sockets, Threading etc.) genutzt. • Dezentral: Jeder Rechner agiert als Knoten in einem Netzwerk, ohne zentrale Serverabhängigkeit. • Flexibel: Erweiterte Befehle ermöglichen das Teilen von Kontaktlisten, selektives Hinzufügen von Kontakten und automatische Synchronisation. • Offline-Nachrichten: Nachrichten, die nicht sofort zugestellt werden können, werden zwischengespeichert und bei Wiederverbindung automatisch gesendet. • Einfache Installation: Mit den beiliegenden Installationsskripten (instance-kws.sh für Linux, instance-kws.bat für Windows) wird ein ZIP-Paket heruntergeladen, entpackt und ein Autostart eingerichtet.

Installation:

Linux:

    Lade das Skript "instance-kws.sh" herunter und speichere es in einem gewünschten Verzeichnis.
    Öffne ein Terminal und navigiere in das Verzeichnis, in dem sich instance-kws.sh befindet.
    Mache das Skript ausführbar: chmod +x instance-kws.sh
    Führe das Skript aus: ./instance-kws.sh Das Skript erstellt im Home-Verzeichnis einen Ordner namens "kws", lädt das ZIP-Paket mit allen erforderlichen Dateien herunter, entpackt es und richtet einen Autostart-Eintrag ein. (Stelle sicher, dass "curl" und "unzip" installiert sind.)

Windows:

    Lade die Datei "instance-kws.bat" herunter.
    Führe die Batch-Datei per Doppelklick aus. Das Skript erstellt einen Ordner "kws" im Benutzerprofil, lädt das ZIP-Paket herunter, entpackt es und legt einen Shortcut im Autostart-Ordner an, sodass kws.py beim Login automatisch startet. (PowerShell muss verfügbar sein.)

Nutzung: Nach der Installation laufen die Komponenten automatisch: • kws.py startet als Hintergrundserver, der den Auth-Key, die Konfiguration und die Kontaktliste verwaltet. • kws-client.py sendet regelmäßig Anfragen an alle Kontakte und versucht, fehlgeschlagene Nachrichten (in data.ksys gespeichert) erneut zu versenden. • Mit kws-service.py kann der Nutzer manuell Befehle eingeben. Verfügbare Befehle sind unter anderem:

    Help: Zeigt eine Übersicht der Befehle.
    Add <auth-id>: Fügt einen neuen Kontakt hinzu (weitere Details werden abgefragt).
    List: Listet alle gespeicherten Kontakte auf.
    Message <user_defined_name> <Nachricht>: Sendet eine Nachricht an einen Kontakt.
    Request <auth-id/user_defined_name> <Befehl>: Sendet eine Anfrage an einen Kontakt. Unterstützte Befehle sind INFO, ADDLIST (übermittelt die eigene Kontaktliste) und LIST (fragt die Kontaktliste des Zielrechners ab). Zusätzliche Einstellungen wie das Ping-Intervall können in der Datei config.cfk angepasst werden.

Viel Erfolg mit KWS – deinem dezentralen Kommunikationsnetzwerk!
