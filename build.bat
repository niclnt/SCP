@echo off
title Construyendo SCP - Sistema de Control de Examen
color 0A

echo [0/4] Activando entorno virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    color 0C
    echo [ERROR] No encuentro 'venv'.
    pause
    exit /b
)

echo.
echo [1/5] Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Release rmdir /s /q Release
if exist *.spec del *.spec
mkdir Release

echo.
echo [2/5] Compilando Servidor...
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Profesor" server/main_server.py

echo.
echo [3/5] Compilando Cliente (Alumno)...
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Alumno" client/main_client.py

:: --- NUEVO PASO ---
echo.
echo [4/5] Compilando LAUNCHER (Actualizador)...
:: El launcher tambien lleva icono
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Launcher" client/launcher.py

if errorlevel 1 (
    color 0C
    echo [ERROR] Fallo al compilar el Launcher.
    pause
    exit /b
)

echo.
echo [5/5] Empaquetando todo en Release...
move dist\SCP_Profesor.exe Release\
move dist\SCP_Alumno.exe Release\
move dist\SCP_Launcher.exe Release\

rmdir /s /q build
rmdir /s /q dist
del *.spec

echo.
echo ========================================================
echo      !COMPILACION EXITOSA (CON LAUNCHER)!
echo ========================================================
pause