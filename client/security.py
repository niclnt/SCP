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
    "blackboxapp",          # Blackbox AI
    "tabnine",              # Tabnine
    "codeium",              # Codeium
    "mintlify",             # Generadores de doc
    "genie",                # ChatGPT en VS Code
    "codium",               # Otra variante
    "supermaven"            # Otra IA rápida
]

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
    Ejecuta un comando oculto para listar extensiones instaladas.
    Retorna una lista con las IAs encontradas.
    """
    violations = []
    
    try:
        # Configuración para que NO salga una ventana negra (cmd) al ejecutar esto
        creation_flags = 0x08000000 if os.name == 'nt' else 0
        
        # Ejecutamos 'code --list-extensions'
        result = subprocess.run(
            ["code", "--list-extensions"], 
            capture_output=True, 
            text=True, 
            creationflags=creation_flags
        )
        
        # Convertimos la lista de extensiones instaladas a minúsculas
        installed_extensions = result.stdout.lower()
        
        # Buscamos si alguna prohibida está en la lista
        for banned in FORBIDDEN_EXTENSIONS:
            if banned in installed_extensions:
                # Encontramos una IA
                violations.append(f"Extensión IA: {banned}")
                
    except FileNotFoundError:
        # Esto pasa si VS Code no está instalado o no está en el PATH
        pass
    except Exception as e:
        print(f"Error chequeando extensiones: {e}")

    return violations