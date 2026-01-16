import psutil
import os
import subprocess
import json
import time

class SecurityGuard:
    def __init__(self):
        self.forbidden_processes = [
            "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe",
            "discord.exe", "chatgpt.exe", "whatsapp.exe", "telegram.exe"
        ]
        self.allowed_apps = []

    def update_config(self, allowed_list):
        self.allowed_apps = [app.lower() for app in allowed_list]

    # --- NUEVO: DETECTOR DE EXTENSIONES INSTALADAS ---
    def check_installed_extensions(self):
        """Revisa la carpeta física de extensiones en busca de IAs."""
        violations = []
        try:
            # Ruta estándar de extensiones de VS Code
            home = os.path.expanduser("~")
            ext_dir = os.path.join(home, ".vscode", "extensions")
            
            if not os.path.exists(ext_dir): return []

            # Palabras que no pueden estar en los nombres de carpetas
            keywords = ["copilot", "blackbox", "codeium", "chatgpt", "tabnine", "ai-chat"]

            for folder_name in os.listdir(ext_dir):
                folder_lower = folder_name.lower()
                for kw in keywords:
                    # Buscamos coincidencias
                    if kw in folder_lower:
                        # Ignoramos si es un falso positivo (ej: un tema de colores)
                        # pero "copilot" suele ser culpable siempre.
                        violations.append(f"Extensión Prohibida: {folder_name}")
                        break
        except Exception: pass
        return list(set(violations))

    def get_running_violations(self):
        found = []
        # 1. Chequeo de Procesos
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    p_name = proc.info['name']
                    if not p_name: continue
                    if p_name.lower() in self.allowed_apps: continue
                    if p_name.lower() in self.forbidden_processes: 
                        if p_name not in found: found.append(p_name)
                except: pass
        except: pass
        
        # 2. Chequeo de Extensiones (NUEVO)
        # Esto detecta si instalaron Copilot aunque no abran el chat
        ext_violations = self.check_installed_extensions()
        found.extend(ext_violations)
        
        return found

    def enforce_exam_settings(self):
        """Aplica el bloqueo maestro y la accesibilidad."""
        try:
            appdata = os.environ.get('APPDATA')
            if not appdata: return False
            
            settings_path = os.path.join(appdata, 'Code', 'User', 'settings.json')
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            
            data = {}
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except: data = {}

            security_rules = {
                "chat.disableAIFeatures": True, 
                "github.copilot.enable": {"*": False},
                "chat.editor.enabled": False,
                "chat.panel.enabled": False,
                "editor.accessibilitySupport": "on",
                "workbench.tips.enabled": False
            }

            changes = False
            for key, val in security_rules.items():
                if data.get(key) != val:
                    data[key] = val
                    changes = True
            
            if changes:
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                return True # Hubo cambios
            return False

        except: return False

    def kill_vscode_processes(self):
        try:
            subprocess.run("taskkill /F /IM Code.exe /T", shell=True, stderr=subprocess.DEVNULL)
        except: pass

    def sabotage_ai_extensions(self):
        if self.enforce_exam_settings():
            # Solo matamos el proceso si hubo cambios importantes al inicio
            self.kill_vscode_processes() 
            return True
        return False

# Instancia global
guard = SecurityGuard()