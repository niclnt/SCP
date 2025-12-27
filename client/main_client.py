import sys
import socket
import json
import time
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QFont, QColor

import security

# --- HILO DE RED Y SEGURIDAD ---
class NetworkThread(QThread):
    msg_received = pyqtSignal(str)
    status_update = pyqtSignal(str, str)

    def __init__(self, ip, port, hostname):
        super().__init__()
        self.ip = ip
        self.port = port
        self.hostname = hostname
        self.socket = None
        self.running = True

    def run(self):
        # 1. FASE DE LIMPIEZA INICIAL
        self.status_update.emit("SANITIZANDO VS CODE...", "#ffb86c") # Naranja
        
        # Matamos procesos previos
        security.kill_vscode_processes()
        time.sleep(1)

        # Bloqueo inicial de carpetas
        security.sabotage_ai_extensions()
        
        # 2. CONEXIÓN
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5) # Timeout inicial
        try:
            self.status_update.emit(f"Conectando a {self.ip}...", "#f1fa8c")
            self.socket.connect((self.ip, self.port))
            self.socket.settimeout(None) # Quitamos timeout

            # Registro
            reg_data = json.dumps({"type": "REGISTER", "hostname": self.hostname})
            self.socket.send(reg_data.encode('utf-8'))
            
            self.status_update.emit("🔒 EXAMEN SEGURO - IA BLOQUEADA", "#50fa7b")

            # 3. BUCLE DE SEGURIDAD (MODO PATRULLA)
            while self.running:
                violations = []
                
                # A. DEFENSA ACTIVA (NUEVO):
                # Intentamos bloquear extensiones en cada ciclo.
                # Si sabotage_ai_extensions devuelve True, significa que encontró una IA activa y la bloqueó.
                re_blocked = security.sabotage_ai_extensions()
                
                if re_blocked:
                    print("[DEFENSA] ¡El alumno intentó reactivar la IA! Matando proceso...")
                    security.kill_vscode_processes() # CASTIGO: Se le cierra el programa
                    violations.append("Intento de Reactivación de IA (Bloqueado)")
                
                # B. Escaneos pasivos
                violations.extend(security.get_running_violations()) # Chrome, etc.
                
                # C. Verificar carpetas (Doble check)
                violations.extend(security.check_settings_violations()) 
                
                if violations:
                    print(f"[VIOLACIÓN] {violations}")
                    self.status_update.emit("¡ALERTA! TRAMPA DETECTADA", "#ff5555")
                    try:
                        alert = json.dumps({
                            "type": "ALERT", 
                            "hostname": self.hostname, 
                            "violations": violations
                        })
                        self.socket.send(alert.encode('utf-8'))
                    except: pass
                else:
                    self.status_update.emit("🔒 EXAMEN SEGURO", "#50fa7b")

                time.sleep(2) # Ciclo cada 2 segundos

        except Exception as e:
            self.msg_received.emit(f"Error: {e}")
        finally:
            # Opcional: Desbloquear al salir
            # security.restore_ai_extensions()
            if self.socket: self.socket.close()

# --- INTERFAZ GRÁFICA (Sin cambios) ---
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Acceso Alumno")
        self.resize(350, 300)
        self.setStyleSheet("background-color: #2e2e2e; color: white; font-family: Segoe UI;")
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        widget.setLayout(layout)

        title = QLabel("Sistema de Control de Examen")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.input_name = QLineEdit(socket.gethostname())
        self.input_name.setPlaceholderText("Tu Nombre")
        self.input_name.setStyleSheet("padding: 8px; color: black; background: #ddd; border-radius: 4px;")
        layout.addWidget(self.input_name)

        self.input_ip = QLineEdit("localhost")
        self.input_ip.setPlaceholderText("IP del Profesor")
        self.input_ip.setStyleSheet("padding: 8px; color: black; background: #ddd; border-radius: 4px;")
        layout.addWidget(self.input_ip)

        self.btn_connect = QPushButton("INGRESAR AL EXAMEN")
        self.btn_connect.setFixedHeight(40)
        self.btn_connect.setStyleSheet("background-color: #007acc; border-radius: 5px; font-weight: bold;")
        self.btn_connect.clicked.connect(self.start_exam)
        layout.addWidget(self.btn_connect)

        self.status_label = QLabel("Listo para conectar.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.status_label)
        layout.addStretch()

    def start_exam(self):
        hostname = self.input_name.text()
        ip = self.input_ip.text()
        if not hostname or not ip: return

        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("INICIANDO...")
        
        self.network_thread = NetworkThread(ip, 9999, hostname)
        self.network_thread.msg_received.connect(self.show_error)
        self.network_thread.status_update.connect(self.update_status_ui)
        self.network_thread.start()

    def update_status_ui(self, text, color_hex):
        self.btn_connect.setText(text)
        self.btn_connect.setStyleSheet(f"background-color: {color_hex}; color: black; font-weight: bold; border-radius: 5px;")
        self.status_label.setText(text)

    def show_error(self, msg):
        self.status_label.setText(msg)
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("INGRESAR AL EXAMEN")
        self.btn_connect.setStyleSheet("background-color: #007acc;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())