import psutil
import subprocess
import os

# Lista de procesos prohibidos, se agregaran mas a futuro
FORBIDDEN_PROCESSES = [
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", 
    "discord.exe", "whatsapp.exe", "chatgpt.exe", "telegram.exe"
]
# Control para extensiones de vscode, se agregaran mas a futuro
FORBIDDEN_EXTENSIONS = [
    "github.copilot",       # GitHub Copilot
    "github.copilot-chat",  # Copilot Chat
    "visualstudioexptteam.vscodeintellicode", # IntelliCode
    "blackboxapp",          # Blackbox AI
    "tabnine",              # Tabnine
    "codeium",              # Codeium
    "mintlify",             # Generadores de doc
    "genie",                # ChatGPT en VS Code
    "codium",               # Otra variante
    "supermaven"            # Otra IA rápida
]
def find_vscode_executable():
    """
    Busca inteligentemente dónde está instalado VS Code (code.cmd) en Windows.
    Retorna la ruta completa o None si no lo encuentra.
    """
    # Rutas estándar donde Windows suele instalar VS Code
    possible_paths = [
        # Instalación de Usuario (AppData) - La más común
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd'),
        # Instalación de Sistema (Archivos de Programa)
        os.path.expandvars(r'%PROGRAMFILES%\Microsoft VS Code\bin\code.cmd'),
        # Instalación de Sistema (x86)
        os.path.expandvars(r'%PROGRAMFILES(X86)%\Microsoft VS Code\bin\code.cmd'),
        # Intento genérico en disco C
        r"C:\VSCode\bin\code.cmd" 
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path
            
    # Si no lo encontramos en las rutas, retornamos "code" para ver si por milagro está en el PATH
    return "code"
def get_running_violations():
    """Retorna una lista de procesos prohibidos detectados."""
    found = []
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in FORBIDDEN_PROCESSES:
                if proc.info['name'] not in found:
                    found.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return found

def get_vscode_violations():
    """
    Usa la ruta encontrada para listar extensiones.
    """
    violations = []
    vscode_path = find_vscode_executable()
    
    try:
        creation_flags = 0x08000000 if os.name == 'nt' else 0
        
        # Ejecutamos el comando usando la ruta detectada
        result = subprocess.run(
            [vscode_path, "--list-extensions"], 
            capture_output=True, 
            text=True, 
            creationflags=creation_flags
        )
        
        if result.returncode != 0:
            # Si el comando falló (ej: retorno código de error)
            pass
        
        installed = result.stdout.lower()
        
        # --- DEBUG TEMPORAL: Para que se vea en la consola qué encontró ---
        if len(installed) > 0:
            print(f"[DEBUG] VS Code encontrado en: {vscode_path}")
            print(f"[DEBUG] Extensiones instaladas detectadas:\n{installed[:200]}...") # Muestra los primeros caracteres
        # ----------------------
        
        for banned in FORBIDDEN_EXTENSIONS:
            if banned in installed:
                print(f"[DEBUG] ¡Violación encontrada!: {banned}") # DEBUG
                violations.append(f"Extensión IA: {banned}")
                
    except FileNotFoundError:
        print(f"[ADVERTENCIA] No se pudo ejecutar VS Code desde: {vscode_path}")
    except Exception as e:
        print(f"[ERROR] Falló el chequeo de extensiones: {e}")

    return violations
   