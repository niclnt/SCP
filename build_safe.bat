@echo off
setlocal
echo ================================================
echo 🛠️  MODO DE COMPILACION CON LAUNCHER (V2.0.1)
echo ================================================

REM 1. Limpieza
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM 2. Activar entorno
call venv\Scripts\activate

REM 3. Instalar librerias (incluyendo requests)
echo [1/5] Verificando librerias...
pip install pyinstaller pyngrok pytesseract pillow uiautomation pyautogui PyQt6 requests --quiet

REM 4. Icono
set "ICON_PARAM="
if exist scp.ico set "ICON_PARAM=--icon=scp.ico"

REM 5. COMPILAR CLIENTE
echo.
echo [2/5] Compilando Cliente...
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Estudiante_Alpha2" %ICON_PARAM% --hidden-import=uiautomation --hidden-import=pyautogui --hidden-import=PyQt6 --uac-admin client/main_client.py
if errorlevel 1 goto error

REM 6. COMPILAR SERVIDOR
echo.
echo [3/5] Compilando Servidor...
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Profesor_Alpha2" %ICON_PARAM% --hidden-import=pyngrok --hidden-import=pytesseract --hidden-import=PIL --hidden-import=PyQt6 server/main_server.py
if errorlevel 1 goto error

REM 7. COMPILAR LAUNCHER 
echo.
echo [4/5] Compilando Launcher...
REM --- CAMBIO AQUI: client\launcher.py ---
pyinstaller --noconfirm --onefile --windowed --clean --name "SCP_Launcher" %ICON_PARAM% --hidden-import=requests --uac-admin client\launcher.py
if errorlevel 1 goto error

REM 8. Copiar Tesseract
echo.
echo [EXTRA] Integrando Motor OCR Tesseract...
if exist "Tesseract-OCR" (
    xcopy "Tesseract-OCR" "dist\Tesseract-OCR\" /E /I /Y /Q
) 

echo.
echo ✅ EXITO: Todo compilado correctamente.
pause
exit /b

:error
echo.
echo ❌ ERROR CRITICO. Revisa el mensaje de arriba.
pause