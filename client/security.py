import psutil
import os
import shutil

class SecurityGuard:
    def __init__(self):
        # Lista negra (Solo para avisar, NO para matar)
        self.forbidden_processes = [
            "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", 
            "discord.exe", "chatgpt.exe"
        ]
        
        # Lista de IAs (Para sabotear y matar VS Code)
        self.ai_extensions = [
            "github.copilot", "blackbox", "tabnine", 
            "codeium", "continue", "cursor"
        ]
        
        self.allowed_apps = [] 

    def update_config(self, allowed_list):
        self.allowed_apps = [app.lower() for app in allowed_list]

    def get_extensions_paths(self):
        """Busca en más ubicaciones posibles de extensiones"""
        paths = []
        user_profile = os.environ.get('USERPROFILE')
        
        # Ruta 1: Carpeta estándar .vscode
        paths.append(os.path.join(user_profile, '.vscode', 'extensions'))
        
        # Ruta 2: AppData (A veces Cursor o versiones portables las guardan aqui)
        appdata = os.environ.get('APPDATA')
        paths.append(os.path.join(appdata, 'Code', 'User', 'globalStorage'))
        
        return paths

    def kill_vscode_processes(self):
        """Mata SOLO VS Code (Se usa solo si se detecta IA)"""
        targets = ["Code.exe", "code.exe", "cursor.exe"]
        for target in targets:
            try:
                os.system(f"taskkill /F /IM {target} /T >nul 2>&1")
            except: pass

    def sabotage_ai_extensions(self):
        """
        Escanea carpetas. 
        Retorna True SOLO si encontró una IA viva y la bloqueó.
        """
        changes_made = False
        extension_dirs = self.get_extensions_paths()

        for base_path in extension_dirs:
            if not os.path.exists(base_path): continue
            try:
                folders = os.listdir(base_path)
                for folder in folders:
                    folder_lower = folder.lower()
                    full_path = os.path.join(base_path, folder)

                    if folder_lower.endswith(".bloqueado"): continue

                    is_ai = any(key in folder_lower for key in self.ai_extensions)
                    
                    if is_ai:
                        new_path = full_path + ".BLOQUEADO"
                        try:
                            os.rename(full_path, new_path)
                            changes_made = True 
                            print(f"[SEGURIDAD] IA Bloqueada: {folder}")
                        except: pass
            except: pass
        
        return changes_made

    def get_running_violations(self):
        """Devuelve procesos prohibidos activos (SOLO PARA INFORMAR)"""
        found = []
        for proc in psutil.process_iter(['name']):
            try:
                p_name = proc.info['name']
                if not p_name: continue
                p_name_lower = p_name.lower()

                if p_name_lower in self.allowed_apps: continue

                if p_name_lower in self.forbidden_processes:
                    found.append(p_name)
            except: pass
        return list(set(found))

    def check_settings_violations(self):
        extension_dirs = self.get_extensions_paths()
        violations = []
        for base_path in extension_dirs:
            if not os.path.exists(base_path): continue
            try:
                folders = os.listdir(base_path)
                for folder in folders:
                    if any(k in folder.lower() for k in self.ai_extensions) and not folder.endswith(".BLOQUEADO"):
                        violations.append(f"IA Activa: {folder}")
            except: pass
        return violations

guard = SecurityGuard()