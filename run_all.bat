@echo off
chcp 65001 > nul
cd /d "ruta"

echo [1/3] Extrayendo precio local...
".\venv\Scripts\python.exe" local.py

echo [2/3] Ejecutando comparador...
".\venv\Scripts\python.exe" comparator.py

echo [3/3] Sincronizando con GitHub...
git pull origin master --rebase
git add data_local.json data.json .gitignore
git commit -m "Update tracker data: %date% %time%" 2>nul
git push origin master

echo Todo listo, archivos locales respaldados.
timeout /t 5
