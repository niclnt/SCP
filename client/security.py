import psutil
import os
import subprocess
import json
import time

class SecurityGuard:
    def __init__(self):
        # LISTA NEGRA: Procesos que no queremos ver durante el examen
        self.forbidden_processes = [
            "chrome.exe", 
            "firefox.exe", 
            "msedge.exe", 
            "opera.exe", 
            "brave.exe",
            "discord.exe", 
            "chatgpt.exe",
            "whatsapp.exe",
            "telegram.exe"
        ]
        self.allowed_apps = []

    def update_config(self, allowed_list):
        """Permite al profesor autorizar apps temporalmente (ej: calculadora)"""
        self.allowed_apps = [app.lower() for app in allowed_list]

    # --- 1. DETECTOR DE PROCESOS (LO QUE FALTABA) ---
    def get_running_violations(self):
        """
        Escanea todos los procesos de Windows.
        Devuelve una lista con los nombres de los procesos prohibidos encontrados.
        """
        found = []
        try:
            # Iteramos sobre todos los procesos corriendo
            for proc in psutil.process_iter(['name']):
                try:
                    p_name = proc.info['name']
                    if not p_name: continue
                    
                    p_name_lower = p_name.lower()
                    
                    # 1. Si está en la lista de PERMITIDOS, lo ignoramos
                    if p_name_lower in self.allowed_apps: 
                        continue

                    # 2. Si está en la lista de PROHIBIDOS, lo anotamos
                    if p_name_lower in self.forbidden_processes:
                        # Evitamos duplicados en el reporte
                        if p_name not in found:
                            found.append(p_name)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            print(f"Error escaneando procesos: {e}")
        
        return found

    # --- 2. BLOQUEO DE VS CODE (ESTRATEGIA BUM) ---
    def enforce_exam_settings(self):
        """
        Aplica los ajustes para apagar la IA y encender la accesibilidad (para el espía).
        """
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

            # REGLAS DE SEGURIDAD
            security_rules = {
                # Apagar IA
                "chat.editor.enabled": False,
                "chat.panel.enabled": False,
                "chat.commandCenter.enabled": False,
                "inlineChat.enabled": False,
                "interactiveEditor.enabled": False,
                "github.copilot.enable": {"*": False},
                "github.copilot.editor.enable": False,
                
                # ENCENDER ACCESIBILIDAD (Vital para watcher.py)
                "editor.accessibilitySupport": "on",
                
                # Limpieza visual
                "workbench.tips.enabled": False,
            }

            changes = False
            for k, v in security_rules.items():
                if data.get(k) != v:
                    data[k] = v
                    changes = True
            
            if changes:
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                print("[CONFIG] Ajustes de seguridad aplicados en VS Code.")
                return True
            return False

        except Exception as e:
            print(f"[ERROR CONFIG] {e}")
            return False

    def kill_vscode_processes(self):
        """Reinicia VS Code para aplicar cambios"""
        try:
            subprocess.run("taskkill /F /IM Code.exe /T", shell=True, stderr=subprocess.DEVNULL)
        except: pass

    def sabotage_ai_extensions(self):
        """Función principal que llama el cliente al iniciar"""
        if self.enforce_exam_settings():
            self.kill_vscode_processes() 
            return True
        return False

    # Stubs para compatibilidad si alguna vez se llaman
    def check_settings_violations(self): return []
    def force_delete_handler(self, a, b, c): pass

# Instancia global
guard = SecurityGuard()