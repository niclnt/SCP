import sys
import os
import subprocess
import requests 
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# --- CONFIGURACIÓN ---
CURRENT_VERSION = "2.0.1" 
VERSION_URL = "https://niclnt.github.io/SCP/version.json" 

# Nombres de los ejecutables reales
EXE_STUDENT = "SCP_Estudiante_Alpha2.exe"
EXE_TEACHER = "SCP_Profesor_Alpha2.exe"

class UpdateThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            self.status.emit("Buscando actualizaciones...")
            self.progress.emit(10)
            
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code != 200:
                self.finished.emit(False, "Error de conexión")
                return

            self.progress.emit(40)
            data = response.json()
            remote_version = data.get("version", "0.0")
            installer_url = data.get("installer_url", "")

            if remote_version != CURRENT_VERSION:
                self.status.emit(f"¡Nueva versión {remote_version}!")
                self.progress.emit(60)
                self.finished.emit(True, installer_url)
            else:
                self.status.emit("Sistema actualizado.")
                self.progress.emit(100)
                self.finished.emit(False, "OK")

        except Exception as e:
            self.finished.emit(False, str(e))

class LauncherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 150)
        
        # Detectar qué modo abrir según argumentos
        # Si recibimos "profesor", abrimos el server. Si no, default estudiante.
        self.target_exe = EXE_STUDENT
        if len(sys.argv) > 1:
            if "profesor" in sys.argv[1].lower():
                self.target_exe = EXE_TEACHER
        
        # UI
        layout = QVBoxLayout(); self.setLayout(layout)
        self.setStyleSheet("""
            QWidget { background-color: #2e2e2e; border-radius: 10px; border: 1px solid #444; }
            QLabel { color: white; }
            QProgressBar { border: 2px solid #444; border-radius: 5px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #28a745; width: 10px; }
        """)

        title_text = "SCP - Profesor" if self.target_exe == EXE_TEACHER else "SCP - Estudiante"
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("border: none;")
        layout.addWidget(self.lbl_title)

        self.lbl_status = QLabel("Iniciando...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #aaa; border: none;")
        layout.addWidget(self.lbl_status)

        self.bar = QProgressBar(); self.bar.setValue(0)
        layout.addWidget(self.bar)

        self.thread = UpdateThread()
        self.thread.progress.connect(self.bar.setValue)
        self.thread.status.connect(self.lbl_status.setText)
        self.thread.finished.connect(self.on_check_finished)
        self.thread.start()

    def on_check_finished(self, update_available, info):
        if update_available:
            self.download_and_install(info)
        else:
            self.launch_main_app()

    def download_and_install(self, url):
        self.lbl_status.setText("Descargando actualización...")
        try:
            installer_name = "Update_SCP.exe"
            response = requests.get(url, stream=True)
            with open(installer_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.lbl_status.setText("Instalando...")
            subprocess.Popen(installer_name)
            QApplication.quit()
        except Exception as e:
            self.launch_main_app() # Si falla, abrimos la app igual

    def launch_main_app(self):
        self.lbl_status.setText("Abriendo...")
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        app_path = os.path.join(current_dir, self.target_exe)
        
        if os.path.exists(app_path):
            subprocess.Popen(app_path)
            QApplication.quit()
        else:
            # Fallback por si estamos en modo desarrollo (fuera de dist)
            if os.path.exists(os.path.join(current_dir, "dist", self.target_exe)):
                subprocess.Popen(os.path.join(current_dir, "dist", self.target_exe))
                QApplication.quit()
            else:
                self.lbl_status.setText(f"❌ Error: Falta {self.target_exe}")
                self.lbl_status.setStyleSheet("color: #ff5555; border: none;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())