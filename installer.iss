; GUION DE INSTALACION PARA SCP (SISTEMA DE CONTROL DE EXAMEN)
; Autor: LNT
; Version: 1.0 Alpha

#define MyAppName "SCP - ExamGuard"
#define MyAppVersion "1.0"
#define MyAppPublisher "Nicolas Bustos"
#define MyAppURL "https://github.com/niclnt/SCP" ;aca proximamente el link de la web
#define MyAppExeName "SCP_Alumno.exe" 
#define MyServerExeName "SCP_Profesor.exe"

[Setup]
; ID Unico de la aplicacion (Generado aleatoriamente para que Windows lo reconozca)
AppId={{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
; Donde se instalara por defecto (Archivos de Programa\SCP)
DefaultDirName={autopf}\{#MyAppName}
; Nombre del grupo en el Menu Inicio
DefaultGroupName={#MyAppName}
; Carpeta donde aparecera el instalador final (junto a los otros exe)
OutputDir=Release
; Nombre del archivo instalador
OutputBaseFilename=Instalar_SCP_v1.0
; Icono del instalador
SetupIconFile=scp.ico
; Compresion maxima para que pese poco
Compression=lzma
SolidCompression=yes
; Estilo moderno de Windows
WizardStyle=modern
; Permisos de Administrador requeridos para instalar
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Components]
; El usuario podra elegir que instalar
Name: "alumno"; Description: "Cliente para Alumnos (Examen)"; Types: full custom; Flags: fixed
Name: "profesor"; Description: "Servidor para Profesores (Monitor)"; Types: full custom

[Files]
; Archivos del ALUMNO (Solo se copian si se elige el componente 'alumno')
Source: "Release\SCP_Alumno.exe"; DestDir: "{app}"; Components: alumno; Flags: ignoreversion
; Archivos del PROFESOR (Solo se copian si se elige el componente 'profesor')
Source: "Release\SCP_Profesor.exe"; DestDir: "{app}"; Components: profesor; Flags: ignoreversion
; El icono tambien se copia
Source: "scp.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Accesos directos en el Menu Inicio
Name: "{group}\SCP Alumno"; Filename: "{app}\SCP_Alumno.exe"; IconFilename: "{app}\scp.ico"; Components: alumno
Name: "{group}\SCP Profesor"; Filename: "{app}\SCP_Profesor.exe"; IconFilename: "{app}\scp.ico"; Components: profesor
Name: "{group}\Desinstalar SCP"; Filename: "{uninstallexe}"

; Accesos directos en el Escritorio (Solo si el usuario marco la casilla)
Name: "{autodesktop}\SCP Alumno"; Filename: "{app}\SCP_Alumno.exe"; IconFilename: "{app}\scp.ico"; Tasks: desktopicon; Components: alumno
Name: "{autodesktop}\SCP Profesor Monitor"; Filename: "{app}\SCP_Profesor.exe"; IconFilename: "{app}\scp.ico"; Tasks: desktopicon; Components: profesor

[Run]
; Opcion para ejecutar al finalizar la instalacion
Filename: "{app}\SCP_Alumno.exe"; Description: "Iniciar SCP Alumno ahora"; Flags: nowait postinstall skipifsilent; Components: alumno
Filename: "{app}\SCP_Profesor.exe"; Description: "Iniciar Monitor Profesor ahora"; Flags: nowait postinstall skipifsilent unchecked; Components: profesor