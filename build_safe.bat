@echo off
setlocal
echo ================================================
echo 🛠️  MODO DE COMPILACION SEGURO (V2.0.1)
echo ================================================
echo.

REM 1. Limpieza
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM 2. Activar entorno
call venv\Scripts\activate

REM 3. Instalar dependencias
echo [1/4] Verificando librerias...
pip install pyinstaller pyngrok pytesseract pillow uiautomation pyautogui PyQt6 --quiet

REM 4. Deteccion de Icono
set "ICON_PARAM="
if exist scp.ico (
    echo 🎨 Icono 'scp.ico' encontrado.
    set "ICON_PARAM=--icon=scp.ico"
)

REM 5. COMPILAR CLIENTE
echo.
echo [2/4] Compilando Cliente...
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Estudiante_Alpha2" %ICON_PARAM% --hidden-import=uiautomation --hidden-import=pyautogui --hidden-import=PyQt6 --uac-admin client/main_client.py

if errorlevel 1 exit /b

REM 6. COMPILAR SERVIDOR
echo.
echo [3/4] Compilando Servidor...
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Profesor_Alpha2" %ICON_PARAM% --hidden-import=pyngrok --hidden-import=pytesseract --hidden-import=PIL --hidden-import=PyQt6 server/main_server.py

if errorlevel 1 exit /b

REM --- [PASO EXTRA] COPIAR TESSERACT AUTOMATICAMENTE ---
echo.
echo [EXTRA] Integrando Motor OCR Tesseract...
if exist "Tesseract-OCR" (
    xcopy "Tesseract-OCR" "dist\Tesseract-OCR\" /E /I /Y /Q
    echo ✅ Tesseract copiado a la carpeta de distribucion.
) else (
    echo ⚠️ ADVERTENCIA: No se encontro la carpeta 'Tesseract-OCR' en la raiz del proyecto.
    echo El servidor no tendra OCR portatil.
)

echo.
echo ================================================
echo ✅ EXITO: VERSION 2.0.1 LISTA
echo ================================================
pause