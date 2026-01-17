@echo off
setlocal
echo ================================================
echo 🛠️  MODO DE COMPILACION SEGURO (DIAGNOSTICO)
echo ================================================
echo.

REM 1. Limpieza
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM 2. Activar entorno
call venv\Scripts\activate

REM 3. Instalar solo lo basico (Sin encriptacion por ahora)
echo [1/3] Verificando librerias base...
pip install pyinstaller pyngrok pytesseract pillow uiautomation pyautogui PyQt6 --quiet

REM 4. Deteccion de Icono
set "ICON_PARAM="
if exist scp.ico (
    echo 🎨 Icono 'scp.ico' encontrado. Se usara.
    set "ICON_PARAM=--icon=scp.ico"
) else (
    echo ⚠️ NO se encontro 'scp.ico'. Se usara el icono estandar.
)

REM 5. COMPILAR CLIENTE
echo.
echo [2/3] Compilando Cliente...
echo ---------------------------------------
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Estudiante_Alpha2" %ICON_PARAM% --hidden-import=uiautomation --hidden-import=pyautogui --hidden-import=PyQt6 --uac-admin client/main_client.py

if errorlevel 1 (
    echo.
    echo ❌ ERROR CRITICO AL COMPILAR EL CLIENTE.
    echo Revisa el mensaje de error arriba en rojo.
    pause
    exit /b
)

REM 6. COMPILAR SERVIDOR
echo.
echo [3/3] Compilando Servidor...
echo ---------------------------------------
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Profesor_Alpha2" %ICON_PARAM% --hidden-import=pyngrok --hidden-import=pytesseract --hidden-import=PIL --hidden-import=PyQt6 server/main_server.py

if errorlevel 1 (
    echo.
    echo ❌ ERROR CRITICO AL COMPILAR EL SERVIDOR.
    pause
    exit /b
)

echo.
echo ================================================
echo ✅ EXITO: CARPETA 'dist' CREADA
echo ================================================
echo Buscala en: %CD%\dist
pause