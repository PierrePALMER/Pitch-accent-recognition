@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

set "TS=C:\Program Files\Tailscale\tailscale.exe"
set "TSHOST="
if exist "%TS%" (
  for /f "delims=" %%i in ('powershell -NoProfile -Command "try{((& '%TS%' status --json ^| ConvertFrom-Json).Self.DNSName).TrimEnd('.')}catch{''}" 2^>nul') do set "TSHOST=%%i"
)

echo.
echo  Lecture accompagnee -- serveur de page
echo  ---------------------------------------------------------------
echo  Depuis cet ordinateur : http://127.0.0.1:8777/lecture.html
if defined TSHOST (
  echo  Depuis l'iPhone       : https://%TSHOST%/lecture.html
) else (
  echo  Depuis l'iPhone       : Tailscale introuvable ou hors ligne.
)
echo.
echo  Prerequis : VOICEVOX doit etre lance (fenetre ouverte).
echo  Laissez cette fenetre ouverte pendant la lecture. Ctrl+C pour arreter.
echo  ---------------------------------------------------------------
echo.

python -m http.server 8777 --bind 127.0.0.1
endlocal
