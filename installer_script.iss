; Script de Instalación para SCP Alpha 2.0
; Requiere Inno Setup Compiler

#define MyAppName "SCP - Sistema de Control de Procesos"
#define MyAppVersion "Alpha 2.0"
#define MyAppPublisher "Nicolas Bustos"
#define MyAppURL "https://github.com/niclnt/SCP"
#define MyAppExeName "SCP_Launcher.exe"

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
AppCopyright=© 2026 SCP Systems. Desarrollado por Nicolás.
LicenseFile=LICENSE.txt

; --- CONFIGURACIÓN TÉCNICA ---
DefaultDirName={autopf}\SCP_System
DisableProgramGroupPage=yes
; Asegúrate de tener el icono o comenta esta línea con punto y coma
SetupIconFile=scp.ico 
OutputDir=installer_dist
OutputBaseFilename=Instalador_SCP_v2.0
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
; NOTA: Asegurate de que los .exe esten en la carpeta 'dist'
Source: "dist\SCP_Estudiante_Alpha2.exe"; DestDir: "{app}"; Components: client; Flags: ignoreversion
Source: "dist\SCP_Profesor_Alpha2.exe"; DestDir: "{app}"; Components: server; Flags: ignoreversion
; Incluimos la licencia también en la carpeta de instalación para referencia futura
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName} - Estudiante"; Filename: "{app}\SCP_Estudiante_Alpha2.exe"; Components: client
Name: "{autoprograms}\{#MyAppName} - Profesor"; Filename: "{app}\SCP_Profesor_Alpha2.exe"; Components: server
Name: "{autodesktop}\SCP Estudiante"; Filename: "{app}\SCP_Estudiante_Alpha2.exe"; Tasks: desktopicon; Components: client
Name: "{autodesktop}\SCP Profesor"; Filename: "{app}\SCP_Profesor_Alpha2.exe"; Tasks: desktopicon; Components: server

[Run]
Filename: "{app}\SCP_Estudiante_Alpha2.exe"; Description: "Ejecutar Cliente Ahora"; Flags: nowait postinstall skipifsilent; Components: client
Filename: "{app}\SCP_Profesor_Alpha2.exe"; Description: "Ejecutar Servidor Ahora"; Flags: nowait postinstall skipifsilent; Components: server