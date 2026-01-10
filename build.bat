@echo off
title Construyendo SCP - BLINDADO (PyArmor + PyInstaller)
color 0A

echo [0/5] Activando entorno virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    color 0C
    echo [ERROR] No encuentro 'venv'.
    pause
    exit /b
)

echo.
echo [1/5] Limpiando carpetas viejas...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Release rmdir /s /q Release
if exist obf_dist rmdir /s /q obf_dist
if exist *.spec del *.spec
mkdir Release

echo.
echo [2/5] OFUSCANDO CODIGO (Blindaje)...
:: PyArmor aplanará la estructura y pondrá todo en obf_dist/
pyarmor gen -O obf_dist client/main_client.py client/security.py client/launcher.py server/main_server.py

if errorlevel 1 (
    color 0C
    echo [ERROR] Fallo PyArmor.
    pause
    exit /b
)
echo Codigo encriptado correctamente.

:: --- CORRECCION CRITICA: Agregamos "security" a los imports ocultos ---
set HIDDEN_IMPORTS=--hidden-import=PyQt6 --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --hidden-import=psutil --hidden-import=requests --hidden-import=json --hidden-import=socket --hidden-import=security

:: Ruta donde buscar los scripts ofuscados
set PATHS_FLAG=--paths="obf_dist"

echo.
echo [3/5] Compilando SERVIDOR Protegido...
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Profesor" %PATHS_FLAG% %HIDDEN_IMPORTS% obf_dist/main_server.py

if errorlevel 1 (
    color 0C
    echo [ERROR] Fallo PyInstaller en el Servidor.
    pause
    exit /b
)

echo.
echo [4/5] Compilando CLIENTE Protegido...
:: Aqui es donde fallaba antes, ahora con --hidden-import=security deberia funcionar
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Alumno" %PATHS_FLAG% %HIDDEN_IMPORTS% obf_dist/main_client.py

if errorlevel 1 (
    color 0C
    echo [ERROR] Fallo PyInstaller en el Cliente.
    pause
    exit /b
)

echo.
echo [4.5/5] Compilando LAUNCHER...
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Launcher" %PATHS_FLAG% %HIDDEN_IMPORTS% obf_dist/launcher.py

echo.
echo [5/5] Empaquetando...
if exist dist\SCP_Profesor.exe move dist\SCP_Profesor.exe Release\
if exist dist\SCP_Alumno.exe move dist\SCP_Alumno.exe Release\
if exist dist\SCP_Launcher.exe move dist\SCP_Launcher.exe Release\

:: Limpieza final
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q obf_dist
del *.spec

echo.
echo ========================================================
echo      COMPILACION BLINDADA EXITOSA
echo      Verifica la carpeta "Release"
echo ========================================================
pause