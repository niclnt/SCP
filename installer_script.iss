; Script de Instalación para SCP Alpha 2.0.1
; Requiere Inno Setup Compiler

#define MyAppName "SCP Monitor - Sistema de Control de Procesos"
#define MyAppVersion "Alpha 2.0.1"
#define MyAppPublisher "Elentech Systems"
#define MyAppURL "https://github.com/niclnt/SCP"
#define MyAppExeName "SCP-Monitor_Launcher.exe"

[Setup]
; --- IDENTIDAD ---
AppId={{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; --- DERECHOS Y LICENCIA (NUEVO) ---
AppCopyright=© 2026 SCP Systems. Desarrollado por Elentech Systems.
LicenseFile=LICENSE.txt

; --- CONFIGURACIÓN TÉCNICA ---
DefaultDirName={autopf}\SCP_System
DisableProgramGroupPage=yes
; Asegúrate de tener el icono o comenta esta línea con punto y coma
SetupIconFile=scp.ico 
OutputDir=installer_dist
OutputBaseFilename=Instalador_SCP_Monitor_v2.0.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Types]
Name: "student"; Description: "Instalación para Estudiante (Cliente)"
Name: "teacher"; Description: "Instalación para Profesor (Servidor)"
Name: "full"; Description: "Instalación Completa (Ambos)"

[Components]
Name: "client"; Description: "SCP Cliente (Estudiante)"; Types: student full
Name: "server"; Description: "SCP Servidor (Profesor)"; Types: teacher full

[Files]
; Agregamos el Launcher
Source: "dist\SCP_Launcher.exe"; DestDir: "{app}"; Components: client; Flags: ignoreversion
; Los ejecutables principales siguen igual
Source: "dist\SCP_Estudiante_Alpha2.exe"; DestDir: "{app}"; Components: client; Flags: ignoreversion
Source: "dist\SCP_Profesor_Alpha2.exe"; DestDir: "{app}"; Components: server; Flags: ignoreversion
; ... (Tesseract y Licencia siguen igual) ...

[Icons]
; --- ICONOS INTELIGENTES (AMBOS USAN EL LAUNCHER) ---

; 1. Acceso directo para ESTUDIANTE (Sin parámetros o param 'estudiante')
Name: "{autoprograms}\{#MyAppName} - Estudiante"; Filename: "{app}\SCP_Launcher.exe"; Parameters: "estudiante"; Components: client
Name: "{autodesktop}\SCP Estudiante"; Filename: "{app}\SCP_Launcher.exe"; Parameters: "estudiante"; Tasks: desktopicon; Components: client

; 2. Acceso directo para PROFESOR (Con parámetro 'profesor')
Name: "{autoprograms}\{#MyAppName} - Profesor"; Filename: "{app}\SCP_Launcher.exe"; Parameters: "profesor"; Components: server
Name: "{autodesktop}\SCP Profesor"; Filename: "{app}\SCP_Launcher.exe"; Parameters: "profesor"; Tasks: desktopicon; Components: server

[Run]
Filename: "{app}\SCP_Estudiante_Alpha2.exe"; Description: "Ejecutar Cliente Ahora"; Flags: nowait postinstall skipifsilent; Components: client
Filename: "{app}\SCP_Profesor_Alpha2.exe"; Description: "Ejecutar Servidor Ahora"; Flags: nowait postinstall skipifsilent; Components: server