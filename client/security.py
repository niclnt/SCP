import psutil
import os
import json
import re
import time
import subprocess
import shutil

# --- 1. PROCESOS PROHIBIDOS ---
FORBIDDEN_PROCESSES = [
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", 
    "discord.exe", "chatgpt.exe", "cursor.exe"
]

# --- 2. EXTENSIONES A SABOTEAR ---
# Buscamos carpetas que contengan estas palabras
EXTENSION_KEYWORDS = [
    "github.copilot", 
    "blackbox", 
    "tabnine", 
    "codeium", 
    "continue"
]

# --- 3. RUTAS DE EXTENSIONES ---
def get_extensions_paths():
    paths = []
    user_profile = os.environ.get('USERPROFILE')
    
    # 1. Carpeta estándar de usuario (.vscode/extensions)
    paths.append(os.path.join(user_profile, '.vscode', 'extensions'))
    
    # 2. Carpeta de instalación global (A veces usada en labs)
    paths.append(r"C:\Program Files\Microsoft VS Code\resources\app\extensions")
    
    return paths

# --- 4. FUNCIONES DE FUERZA BRUTA ---

def kill_vscode_processes():
    """Mata VS Code sin piedad."""
    print("[SEGURIDAD] Matando VS Code...")
    killed = False
    targets = ["Code.exe", "code.exe", "cursor.exe"]
    for target in targets:
        try:
            # taskkill /F (Forzar) /IM (Imagen) /T (Árbol de procesos)
            subprocess.run(f"taskkill /F /IM {target} /T", shell=True, capture_output=True)
            killed = True
        except: pass
    return killed

def sabotage_ai_extensions():
    """
    Busca las carpetas de IA y las renombra agregando '.BLOQUEADO'.
    VS Code no podrá cargarlas al reiniciar.
    Retorna True si bloqueó alguna extensión (requiere reinicio).
    """
    changes_made = False
    extension_dirs = get_extensions_paths()

    print("[SEGURIDAD] Buscando extensiones de IA para bloquear...")

    for base_path in extension_dirs:
        if not os.path.exists(base_path): continue

        try:
            # Listamos todas las carpetas de extensiones
            folders = os.listdir(base_path)
            for folder in folders:
                folder_lower = folder.lower()
                full_path = os.path.join(base_path, folder)

                # Si ya está bloqueada, la ignoramos
                if folder_lower.endswith(".bloqueado"):
                    continue

                # Verificamos si es una IA
                is_ai = any(key in folder_lower for key in EXTENSION_KEYWORDS)
                
                if is_ai:
                    new_path = full_path + ".BLOQUEADO"
                    try:
                        print(f"[BLOQUEO] Deshabilitando extensión: {folder}")
                        os.rename(full_path, new_path)
                        changes_made = True
                    except PermissionError:
                        print(f"[ERROR] No tengo permisos para bloquear: {folder}. Ejecuta como Admin.")
                    except Exception as e:
                        print(f"[ERROR] Falló bloqueo de {folder}: {e}")

        except Exception as e:
            print(f"[ERROR] Error escaneando {base_path}: {e}")

    return changes_made

def restore_ai_extensions():
    """
    (Opcional) Quita el '.BLOQUEADO' al terminar el examen.
    """
    extension_dirs = get_extensions_paths()
    print("[LIMPIEZA] Restaurando extensiones...")
    
    for base_path in extension_dirs:
        if not os.path.exists(base_path): continue
        try:
            folders = os.listdir(base_path)
            for folder in folders:
                if folder.endswith(".BLOQUEADO"):
                    original_name = folder.replace(".BLOQUEADO", "")
                    old_path = os.path.join(base_path, folder)
                    new_path = os.path.join(base_path, original_name)
                    try:
                        os.rename(old_path, new_path)
                        print(f"[RESTAURADO] {original_name}")
                    except: pass
        except: pass

# --- MONITOREO ---
def get_running_violations():
    # Detectar procesos prohibidos (Chrome, etc)
    found = []
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in FORBIDDEN_PROCESSES:
                found.append(proc.info['name'])
        except: pass
    return list(set(found))

def check_settings_violations():
    # En este enfoque físico, si la carpeta está renombrada, no necesitamos chequear settings.
    # Pero podemos verificar si alguna carpeta se "desbloqueó" sola.
    extension_dirs = get_extensions_paths()
    violations = []
    
    for base_path in extension_dirs:
        if not os.path.exists(base_path): continue
        try:
            folders = os.listdir(base_path)
            for folder in folders:
                # Si encontramos una carpeta de IA que NO tiene .BLOQUEADO al final, es trampa
                if any(k in folder.lower() for k in EXTENSION_KEYWORDS) and not folder.endswith(".BLOQUEADO"):
                    violations.append(f"IA Detectada Activa: {folder}")
        except: pass
        
    return violations