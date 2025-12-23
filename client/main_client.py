import sys
import socket
import json
import time
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
import security  # Importamos nuestro módulo de seguridad

class NetworkThread(QThread):
    msg_received = pyqtSignal(str)

    def __init__(self, ip, port, hostname):
        super().__init__()
        self.ip = ip
        self.port = port
        self.hostname = hostname
        self.socket = None
        self.running = True

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.ip, self.port))
            
            # 1. Enviar registro INICIAL
            reg_data = json.dumps({"type": "REGISTER", "hostname": self.hostname})
            self.socket.send(reg_data.encode('utf-8'))

            #contador de ciclos para optimizar el escaneo
            loop_counter=0
            
            # 2. Iniciar bucle de seguridad y escucha
            while self.running:
                # -- Verificación de Seguridad --
                violations=[]
                #escaneo rapido cada 2 seg
                proc_violations = security.get_running_violations()
                violations.extend(proc_violations)

                # 2. Escaneo Lento: Extensiones VS Code (Cada 20 seg aprox)
                # Solo entramos aca si el contador llega a 10
                if loop_counter >= 10:
                    ext_violations = security.get_vscode_violations()
                    violations.extend(ext_violations)
                    loop_counter = 0 # Reseteamos contador
                #si encontramos algo enviamos ALERTA
                if violations:
                    alert = json.dumps({"type": "ALERT", "hostname": self.hostname, "violations": violations})
                    try:
                        self.socket.send(alert.encode('utf-8'))
                    except: pass
                loop_counter +=1
                time.sleep(2) # Revisar cada 2 segundos

        except Exception as e:
            self.msg_received.emit(f"Error de conexión: {e}")
        finally:
            if self.socket: self.socket.close()

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Acceso Alumno")
        self.resize(300, 250)
        self.setStyleSheet("background-color: #2e2e2e; color: white;")
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # UI Elements
        layout.addWidget(QLabel("Nombre del Alumno / PC:"))
        self.input_name = QLineEdit(socket.gethostname())
        self.input_name.setStyleSheet("padding: 5px; color: black; background: #ddd;")
        layout.addWidget(self.input_name)

        layout.addWidget(QLabel("IP del Profesor (Código):"))
        self.input_ip = QLineEdit("localhost") # Por defecto localhost para probar
        self.input_ip.setStyleSheet("padding: 5px; color: black; background: #ddd;")
        layout.addWidget(self.input_ip)

        self.btn_connect = QPushButton("Conectar al Examen")
        self.btn_connect.setStyleSheet("background-color: #007acc; padding: 10px; font-weight: bold;")
        self.btn_connect.clicked.connect(self.start_exam)
        layout.addWidget(self.btn_connect)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff5555;")
        layout.addWidget(self.status_label)

    def start_exam(self):
        hostname = self.input_name.text()
        ip = self.input_ip.text()
        
        if not hostname or not ip:
            self.status_label.setText("Completa todos los campos")
            return

        # Iniciamos el hilo de red
        self.network_thread = NetworkThread(ip, 9999, hostname)
        self.network_thread.msg_received.connect(self.show_error)
        self.network_thread.start()
        
        # Cambiamos la UI para mostrar que está activo
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("🔒 EXAMEN ACTIVO - MONITOREANDO")
        self.btn_connect.setStyleSheet("background-color: #50fa7b; color: black;")
        self.status_label.setText("Conectado. No abras programas prohibidos.")
        self.status_label.setStyleSheet("color: #50fa7b;")

    def show_error(self, msg):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet("color: #ff5555;")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Conectar al Examen")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())