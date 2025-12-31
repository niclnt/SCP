import sys
import socket
import json
import time
import threading
# Importamos QFrame para hacer líneas separadoras
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QFrame) 
from PyQt6.QtCore import pyqtSignal, QThread, Qt, QObject
from PyQt6.QtGui import QFont, QColor

import security

# --- HILO DE ESCUCHA (Discovery - Igual que antes) ---
class DiscoveryThread(QThread):
    server_found = pyqtSignal(str, str)

    def run(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp_sock.bind(('', 5555))
            while True:
                data, addr = udp_sock.recvfrom(1024)
                try:
                    msg = json.loads(data.decode('utf-8'))
                    if msg.get('type') == 'SCP_SERVER':
                        # AQUÍ ESTÁ EL CAMBIO:
                        # Leemos la IP que viene DENTRO del mensaje ("ip")
                        # Si no viene, usamos la de addr[0] como respaldo.
                        server_ip = msg.get('ip', addr[0])
                        
                        self.server_found.emit(msg['name'], server_ip)
                except: pass
        except: pass

# --- HILO DE RED (Igual que antes) ---
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
        # 1. SANITIZACIÓN
        self.status_update.emit("SANITIZANDO VS CODE...", "#ffb86c")
        security.kill_vscode_processes()
        time.sleep(1)
        security.sabotage_ai_extensions()
        
        # 2. CONEXIÓN
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        try:
            self.status_update.emit(f"Conectando a {self.ip}...", "#f1fa8c")
            self.socket.connect((self.ip, self.port))
            self.socket.settimeout(None)

            reg_data = json.dumps({"type": "REGISTER", "hostname": self.hostname})
            self.socket.send(reg_data.encode('utf-8'))
            
            self.status_update.emit("🔒 EXAMEN SEGURO", "#50fa7b")

            while self.running:
                violations = []
                
                # A. Defensa Activa
                if security.sabotage_ai_extensions():
                    security.kill_vscode_processes()
                    violations.append("Intento Reactivación IA")

                # B. Escaneos
                violations.extend(security.get_running_violations())
                violations.extend(security.check_settings_violations())
                
                if violations:
                    # CASO 1: HAY PROBLEMAS
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
                    # CASO 2: TODO LIMPIO (Aquí estaba el silencio, ahora hablamos)
                    self.status_update.emit("🔒 EXAMEN SEGURO", "#50fa7b")
                    try:
                        # Enviamos latido de "Todo OK"
                        ok_msg = json.dumps({
                            "type": "STATUS",
                            "hostname": self.hostname,
                            "status": "CLEAN" # Código interno para decir "Limpio"
                        })
                        self.socket.send(ok_msg.encode('utf-8'))
                    except: pass

                time.sleep(2)

        except Exception as e:
            self.msg_received.emit(f"Error: {e}")
        finally:
            if self.socket: self.socket.close()

# --- INTERFAZ RENOVADA Y CORREGIDA ---
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Acceso Alumno")
        self.resize(400, 450) # Un poco más grande para que entre todo cómodo
        self.setStyleSheet("background-color: #2e2e2e; color: white; font-family: Segoe UI;")
        
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        widget.setLayout(layout)

        # Título
        title = QLabel("Sistema de Control de Examen")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(10)

        # 1. Sección Nombre
        layout.addWidget(QLabel("Paso 1: Tu Nombre o Legajo"))
        self.input_name = QLineEdit(socket.gethostname())
        self.input_name.setStyleSheet("padding: 10px; color: black; background: #ddd; border-radius: 4px; font-size: 14px;")
        layout.addWidget(self.input_name)
        layout.addSpacing(10)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #555;")
        layout.addWidget(line)
        layout.addSpacing(10)

        # 2. Sección Selección de Servidor
        layout.addWidget(QLabel("Paso 2: Selecciona la Clase (Automático)"))
        self.combo_server = QComboBox()
        self.combo_server.setStyleSheet("""
            QComboBox { padding: 10px; color: black; background: #ddd; border-radius: 4px; font-size: 14px;}
            QComboBox::drop-down { border: 0px; }
        """)
        self.combo_server.addItem("Buscando profesores en la red...", "")
        layout.addWidget(self.combo_server)
        layout.addSpacing(5)
        
        # Label "O"
        lbl_or = QLabel("- O -")
        lbl_or.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_or.setStyleSheet("color: #aaa;")
        layout.addWidget(lbl_or)
        layout.addSpacing(5)

        # 3. Sección IP Manual
        layout.addWidget(QLabel("Ingresa IP Manualmente (Si no aparece arriba)"))
        self.input_ip_manual = QLineEdit()
        self.input_ip_manual.setPlaceholderText("Ej: 192.168.1.55")
        self.input_ip_manual.setStyleSheet("padding: 10px; color: black; background: #ddd; border-radius: 4px; font-size: 14px;")
        layout.addWidget(self.input_ip_manual)
        layout.addSpacing(20)

        # --- BOTÓN CONECTAR (El que faltaba) ---
        self.btn_connect = QPushButton("CONECTAR AL EXAMEN")
        self.btn_connect.setFixedHeight(50)
        self.btn_connect.setStyleSheet("""
            QPushButton { background-color: #007acc; border-radius: 5px; font-weight: bold; font-size: 16px; }
            QPushButton:hover { background-color: #0098ff; }
        """)
        # Conectamos el botón a la nueva lógica inteligente
        self.btn_connect.clicked.connect(self.start_exam_smart)
        layout.addWidget(self.btn_connect)

        # Estado
        self.status_label = QLabel("Completa los pasos para conectar.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #aaa; margin-top: 10px;")
        layout.addWidget(self.status_label)
        layout.addStretch()

        # Iniciar Discovery
        self.discovery = DiscoveryThread()
        self.discovery.server_found.connect(self.add_server_to_list)
        self.discovery.start()
        self.known_servers = []

    def add_server_to_list(self, name, ip):
        if ip not in self.known_servers:
            if not self.known_servers: self.combo_server.clear()
            self.known_servers.append(ip)
            self.combo_server.addItem(f"🏫 {name} ({ip})", ip)

    # --- NUEVA LÓGICA DE CONEXIÓN INTELIGENTE ---
    def start_exam_smart(self):
        hostname = self.input_name.text().strip()
        if not hostname:
             self.status_label.setText("❌ Falta tu Nombre en el Paso 1")
             self.status_label.setStyleSheet("color: #ff5555;")
             return

        target_ip = ""
        
        # Lógica: ¿Escribió una IP manual? Usamos esa.
        if self.input_ip_manual.text().strip():
            target_ip = self.input_ip_manual.text().strip()
            print(f"[DEBUG] Usando IP Manual: {target_ip}")
            
        # Si no, ¿seleccionó algo válido del combo? Usamos eso.
        elif self.combo_server.currentData():
            target_ip = self.combo_server.currentData()
            print(f"[DEBUG] Usando IP Automática: {target_ip}")
            
        # Si no hay ninguna de las dos...
        if not target_ip:
            self.status_label.setText("❌ Selecciona un servidor o ingresa IP")
            self.status_label.setStyleSheet("color: #ff5555;")
            return
        
        # ¡Todo listo, iniciamos!
        self.start_connection_thread(target_ip, hostname)

    def start_connection_thread(self, ip, hostname):
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("INICIANDO...")
        if self.discovery.isRunning(): self.discovery.terminate()

        self.network_thread = NetworkThread(ip, 9999, hostname)
        self.network_thread.msg_received.connect(self.show_error)
        self.network_thread.status_update.connect(self.update_status_ui)
        self.network_thread.start()

    def update_status_ui(self, text, color_hex):
        self.btn_connect.setText(text)
        self.btn_connect.setStyleSheet(f"background-color: {color_hex}; color: black; font-weight: bold; border-radius: 5px; font-size: 16px;")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color_hex};")

    def show_error(self, msg):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet("color: #ff5555;")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("CONECTAR AL EXAMEN")
        self.btn_connect.setStyleSheet("background-color: #007acc; border-radius: 5px; font-weight: bold; font-size: 16px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())