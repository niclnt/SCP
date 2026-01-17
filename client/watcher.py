import uiautomation as auto
import time
import threading
import pyautogui
import io
import base64

# Palabras clave que delatan al chat
THREAT_KEYWORDS = [
    "Github Copilot", 
    "Ask Copilot",
    "Github Copilot Chat"
    "Ask about your code",
    "Generate Agent Instrutions to onboard AI onto your codebase",
    "AI responses",
    "Explore and understand your code",
    "Inline Chat",
    "Chat Panel",       # VS Code nombra así al panel contenedor
    "ChatView",         # Nombre técnico interno
    "CopilotChat",
    "Interactive Editor", # La ventanita de Ctrl+I
    "Describe what to build next",
    "Agent"
]

class VSCodeWatcher:
    def __init__(self):
        self.running = False
        self.violation_detected = False
        self.last_violation_name = ""
        self.last_screenshot_base64 = None # Aquí guardaremos la evidencia

    def take_evidence_screenshot(self):
        """Toma una captura, la comprime y la convierte a texto base64"""
        try:
            # Captura toda la pantalla
            screenshot = pyautogui.screenshot()
            
            # Guardar en memoria (buffer) como JPG comprimido
            buffer = io.BytesIO()
            screenshot.save(buffer, format="JPEG", quality=40) # Calidad 40 para que viaje rápido
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return img_str
        except Exception as e:
            print(f"Error tomando foto: {e}")
            return None

    def scan_loop(self):
        while self.running:
            try:
                # 1. Buscar VS Code
                vscode = auto.WindowControl(searchDepth=1, RegexName=".*Visual Studio Code.*")
                
                if vscode.Exists(0, 0) and vscode.IsActive():
                    found_threat = False
                    
                    # 2. Escanear controles (Gracias a accessibilitySupport: on)
                    for control, depth in auto.WalkControl(vscode, maxDepth=8):
                        if not control.Name or len(control.Name) < 3: continue
                        
                        # FILTRO DE SEGURIDAD:
                        # Solo nos importan Paneles, Grupos o Botones.
                        # Ignoramos "Edit", "Document" o "Text" porque eso es EL CÓDIGO del alumno.
                        if control.ControlTypeName in ["EditControl", "DocumentControl", "TextControl"]:
                            continue 

                        # Chequeo de palabras prohibidas
                        name = control.Name.lower()
                        
                        # Caso especial: El panel principal a veces se llama solo "Chat"
                        # Verificamos que sea un PANEL, no texto
                        if "chat" == name and control.ControlTypeName in ["GroupControl", "PaneControl"]:
                             self.violation_detected = True
                             self.last_violation_name = "Panel Lateral de Chat"
                             # ... tomar foto ...
                             break
                        
                        # Búsqueda general de las otras keywords
                        for kw in THREAT_KEYWORDS:
                            if kw.lower() in name:
                                self.violation_detected = True
                                self.last_violation_name = f"IA Detectada: {control.Name}"
                                # ... tomar foto ...
                                found_threat = True
                                break
                        if found_threat: break
                    
                    if not found_threat:
                        self.violation_detected = False
                        self.last_screenshot_base64 = None # Limpiamos si se porta bien
                
                else:
                    self.violation_detected = False

            except Exception: pass
            time.sleep(2)

    def start(self):
        if not self.running:
            self.running = True
            t = threading.Thread(target=self.scan_loop)
            t.daemon = True
            t.start()

    def stop(self):
        self.running = False

    def get_status_and_evidence(self):
        """Devuelve (Mensaje de Violación, Foto en Base64)"""
        if self.violation_detected:
            return self.last_violation_name, self.last_screenshot_base64
        return None, None

watcher = VSCodeWatcher()