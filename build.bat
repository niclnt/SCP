@echo off
title Construyendo SCP - BLINDADO (PyArmor + PyInstaller)
color 0A

echo [0/5] Activando entorno...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] No hay venv.
    pause
    exit /b
)

echo.
echo [1/5] Limpiando...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Release rmdir /s /q Release
if exist obf_dist rmdir /s /q obf_dist
if exist *.spec del *.spec
mkdir Release

echo.
echo [2/5] OFUSCANDO CODIGO (Blindaje)...
:: Generamos versiones encriptadas en la carpeta obf_dist
:: Protegemos security.py y los mains.
pyarmor gen -O obf_dist client/main_client.py client/security.py client/launcher.py server/main_server.py
echo Codigo encriptado correctamente.

echo.
echo [3/5] Compilando SERVIDOR Protegido...
:: Nota: Apuntamos a la carpeta obf_dist donde esta el codigo seguro
:: --paths añade la carpeta actual para que encuentre dependencias si hace falta
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Profesor" --paths="." obf_dist/server/main_server.py

echo.
echo [4/5] Compilando CLIENTE Protegido...
:: El cliente necesita security.py, que ya esta en obf_dist/client
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Alumno" --paths="." obf_dist/client/main_client.py

echo.
echo [4.5/5] Compilando LAUNCHER...
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Launcher" --paths="." obf_dist/client/launcher.py

echo.
echo [5/5] Empaquetando...
move dist\SCP_Profesor.exe Release\
move dist\SCP_Alumno.exe Release\
move dist\SCP_Launcher.exe Release\

:: Limpieza final de archivos temporales (incluyendo el codigo ofuscado temporal)
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q obf_dist
del *.spec

echo.
echo ========================================================
echo      COMPILACION BLINDADA EXITOSA
echo ========================================================
pause