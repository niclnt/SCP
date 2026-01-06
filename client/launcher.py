import sys
import os
import subprocess
import json
import requests # Para consultar a internet
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

# --- CONFIGURACIÓN ---
CURRENT_VERSION = "1.0" # ESTA VERSION DEBE COINCIDIR CON LA DE TU JSON CUANDO NO HAYA UPDATES
VERSION_URL = "https://niclnt.github.io/SCP/version.json" 
# Nombre del ejecutable principal que vamos a abrir si todo está bien
MAIN_APP_EXE = "SCP_Alumno.exe"

class UpdateThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str) # (Hay update?, url/error)

    def run(self):
        try:
            self.status.emit("Verificando versión...")
            self.progress.emit(10)
            
            # 1. Consultar version.json
            response = requests.get(VERSION_URL, timeout=5)
            if response.status_code != 200:
                self.finished.emit(False, "Error de conexión")
                return

            self.progress.emit(30)
            data = response.json()
            remote_version = data.get("version", "0.0")
            installer_url = data.get("installer_url", "")

            print(f"[LAUNCHER] Local: {CURRENT_VERSION} | Remota: {remote_version}")

            # 2. Comparar versiones
            # Si la remota es distinta a la local, asumimos que es nueva
            if remote_version != CURRENT_VERSION:
                self.status.emit(f"¡Nueva versión {remote_version} encontrada!")
                self.progress.emit(50)
                self.finished.emit(True, installer_url)
            else:
                self.status.emit("Sistema actualizado.")
                self.progress.emit(100)
                self.finished.emit(False, "OK")

        except Exception as e:
            print(f"[ERROR] {e}")
            self.finished.emit(False, str(e))

class LauncherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) # Sin bordes
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 150)
        
        # Layout Estilo "Tarjeta"
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Fondo oscuro
        self.setStyleSheet("""
            QWidget { background-color: #2e2e2e; border-radius: 10px; border: 1px solid #444; }
            QLabel { color: white; }
            QProgressBar { border: 2px solid #444; border-radius: 5px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #007acc; width: 10px; }
        """)

        # Titulo
        self.lbl_title = QLabel("SCP - ExamGuard")
        self.lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("border: none;")
        layout.addWidget(self.lbl_title)

        # Estado
        self.lbl_status = QLabel("Iniciando...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #aaa; border: none;")
        layout.addWidget(self.lbl_status)

        # Barra
        self.bar = QProgressBar()
        self.bar.setValue(0)
        layout.addWidget(self.bar)

        # Iniciar Hilo
        self.thread = UpdateThread()
        self.thread.progress.connect(self.bar.setValue)
        self.thread.status.connect(self.lbl_status.setText)
        self.thread.finished.connect(self.on_check_finished)
        self.thread.start()

    def on_check_finished(self, update_available, info):
        if update_available:
            # INFO contiene la URL del instalador
            self.download_and_install(info)
        else:
            # INFO contiene "OK" o un error, lanzamos la app igual
            self.launch_main_app()

    def download_and_install(self, url):
        self.lbl_status.setText("Descargando actualización...")
        try:
            # Descargamos el instalador a la carpeta temporal
            installer_name = "Update_SCP.exe"
            response = requests.get(url, stream=True)
            with open(installer_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Ejecutamos el instalador y cerramos el launcher
            self.lbl_status.setText("Abriendo instalador...")
            subprocess.Popen(installer_name)
            QApplication.quit()
            
        except Exception as e:
            self.lbl_status.setText(f"Error descarga: {e}")
            # Si falla, intentamos abrir la app vieja por si acaso
            QThread.msleep(2000)
            self.launch_main_app()

    def launch_main_app(self):
        self.lbl_status.setText("Abriendo Examen...")
        
        # Lógica inteligente para encontrar el archivo
        # 1. Buscamos en la carpeta actual (donde está el launcher.exe)
        current_dir = os.getcwd()
        app_path = os.path.join(current_dir, MAIN_APP_EXE)
        
        # 2. Si no está ahí (ej: estamos probando desde python), buscamos en Release
        if not os.path.exists(app_path):
            app_path = os.path.join(current_dir, "Release", MAIN_APP_EXE)
        
        if os.path.exists(app_path):
            print(f"[LAUNCHER] Abriendo: {app_path}")
            subprocess.Popen(app_path)
            QApplication.quit()
        else:
            self.lbl_status.setText(f"❌ Error: No encuentro {MAIN_APP_EXE}")
            self.lbl_status.setStyleSheet("color: #ff5555; border: none;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())