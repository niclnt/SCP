@echo off
title Construyendo SCP - Sistema de Control de Examen
color 0A

echo ========================================================
echo      INICIANDO PROCESO DE COMPILACION (VERSION ALPHA)
echo ========================================================
echo.

:: --- PASO CRITICO: ACTIVAR EL ENTORNO VIRTUAL ---
echo [0/4] Activando entorno virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    color 0C
    echo [ERROR] No encuentro la carpeta 'venv'.
    echo Asegurate de estar en la carpeta correcta.
    pause
    exit /b
)

:: 1. LIMPIEZA PREVIA
echo.
echo [1/4] Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Release rmdir /s /q Release
if exist *.spec del *.spec
mkdir Release

:: 2. COMPILAR PROFESOR (SERVER)
echo.
echo [2/4] Compilando Servidor del Profesor...
:: Si no tienes icono aun, borra la parte de --icon=scp.ico
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Profesor" server/main_server.py

if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Fallo al compilar el Profesor.
    echo Verifique si 'pyinstaller' esta instalado: pip install pyinstaller
    pause
    exit /b
)

:: 3. COMPILAR ALUMNO (CLIENT)
echo.
echo [3/4] Compilando Cliente del Alumno...
pyinstaller --noconsole --onefile --icon=scp.ico --name="SCP_Alumno" client/main_client.py

if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] Fallo al compilar el Alumno.
    pause
    exit /b
)

:: 4. ORGANIZAR ARCHIVOS FINALES
echo.
echo [4/4] Empaquetando en carpeta Release...
move dist\SCP_Profesor.exe Release\
move dist\SCP_Alumno.exe Release\

:: LIMPIEZA FINAL
rmdir /s /q build
rmdir /s /q dist
del *.spec

echo.
echo ========================================================
echo      !COMPILACION EXITOSA!
echo      Los archivos estan en la carpeta "Release"
echo ========================================================
echo.
pause