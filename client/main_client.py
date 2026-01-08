import sys
import socket
import threading
import json
import time
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QFont, QIcon

# Importamos la guardia dinámica
from security import guard

# --- 1. DEFINICIÓN DE TEMAS (CLIENTE) ---

THEME_DARK = """
QWidget { background-color: #1e1e2e; font-family: 'Segoe UI', sans-serif; color: #cdd6f4; }
QLineEdit { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 10px; color: white; font-size: 14px; }
QLineEdit:focus { border: 1px solid #89b4fa; }
QComboBox { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 10px; color: white; font-size: 14px; }
QComboBox::drop-down { border: none; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 14px; }
QPushButton:hover { background-color: #b4befe; }
QPushButton#Locked { background-color: #f38ba8; color: #181825; }
QPushButton#Config { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 8px; }
QPushButton#Config:hover { background-color: #45475a; }
QLabel { font-size: 14px; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #fab387; }
QLabel#Status { font-weight: bold; font-size: 16px; }
QFrame { background-color: #181825; border-radius: 12px; }
"""

THEME_LIGHT = """
QWidget { background-color: #eff1f5; font-family: 'Segoe UI', sans-serif; color: #4c4f69; }
QLineEdit { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 10px; color: #4c4f69; font-size: 14px; }
QLineEdit:focus { border: 1px solid #1e66f5; }
QComboBox { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 10px; color: #4c4f69; font-size: 14px; }
QComboBox::drop-down { border: none; }
QPushButton { background-color: #1e66f5; color: #ffffff; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 14px; }
QPushButton:hover { background-color: #7287fd; }
QPushButton#Locked { background-color: #d20f39; color: #ffffff; }
QPushButton#Config { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #dce0e8; padding: 8px; }
QPushButton#Config:hover { background-color: #dce0e8; }
QLabel { font-size: 14px; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #fe640b; }
QLabel#Status { font-weight: bold; font-size: 16px; }
QFrame { background-color: #e6e9ef; border-radius: 12px; border: 1px solid #dce0e8; }
"""

# --- 2. LOGICA DE RED (Igual que antes, con la corrección de seguridad) ---

class DiscoveryThread(QThread):
    server_found = pyqtSignal(str, str) # Nombre, IP

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', 5555))
        except:
            return 
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get('type') == 'SCP_SERVER':
                    self.server_found.emit(msg['name'], msg['ip'])
            except: pass

class NetworkThread(QThread):
    status_signal = pyqtSignal(str) # Para mostrar mensajes en la UI

    def __init__(self, server_ip, student_name):
        super().__init__()
        self.server_ip = server_ip
        self.student_name = student_name
        self.running = True
        self.sock = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.server_ip, 9999))
            
            listener = threading.Thread(target=self.receive_loop)
            listener.daemon = True
            listener.start()

            reg_msg = json.dumps({"type": "REGISTER", "hostname": self.student_name})
            self.sock.sendall(reg_msg.encode('utf-8'))

            while self.running:
                # 1. IA: Solo matamos VS Code si ACABAMOS de bloquear algo
                if guard.sabotage_ai_extensions():
                    print("[CLIENTE] IA detectada y bloqueada. Reiniciando VS Code...")
                    guard.kill_vscode_processes()

                # 2. Procesos Prohibidos
                process_violations = guard.get_running_violations()
                if process_violations:
                    for proc in process_violations:
                        guard.kill_specific_process(proc)

                # 3. Reportar al Profesor
                folder_violations = guard.check_settings_violations()
                all_violations = folder_violations + process_violations

                if all_violations:
                    msg = json.dumps({"type": "ALERT", "violations": all_violations})
                    self.status_signal.emit(f"⚠️ BLOQUEADO: {all_violations[0]}")
                else:
                    msg = json.dumps({"type": "STATUS", "status": "CLEAN"})
                    self.status_signal.emit("✅ Examen Seguro - Monitoreando")

                try:
                    self.sock.sendall(msg.encode('utf-8'))
                except:
                    break 

                time.sleep(2)

        except Exception as e:
            self.status_signal.emit(f"Error de conexión: {e}")
        finally:
            self.running = False
            if self.sock: self.sock.close()

    def receive_loop(self):
        try:
            while self.running:
                data = self.sock.recv(4096)
                if not data: break
                msg = json.loads(data.decode('utf-8'))
                
                if msg.get('type') == 'CONFIG':
                    allowed = msg.get('allowed_apps', [])
                    guard.update_config(allowed)
                    print(f"[CLIENTE] Nuevas reglas recibidas: {allowed}")     
        except: pass

# --- 3. INTERFAZ GRÁFICA (Con Botón de Configuración) ---

class StudentClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Examen Seguro")
        self.resize(400, 550)
        
        # Estado inicial del tema
        self.is_dark_mode = True 
        
        # Layout Principal
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        # --- BARRA SUPERIOR (TOP BAR) ---
        # Aquí ponemos el botón de configuración a la derecha
        top_bar = QHBoxLayout()
        
        # Titulo pequeño o vacío (El titulo grande va abajo)
        top_bar.addStretch() # Empuja el botón a la derecha
        
        self.btn_theme = QPushButton("⚙️ Tema Oscuro")
        self.btn_theme.setObjectName("Config") # Usamos el ID para darle estilo especial
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setFixedWidth(150)
        top_bar.addWidget(self.btn_theme)
        
        self.layout.addLayout(top_bar)

        # --- ENCABEZADO ---
        lbl_title = QLabel("SCP ExamGuard")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Sistema de Control de Procesos")
        lbl_subtitle.setStyleSheet("color: #bac2de; font-size: 12px;") # Se sobreescribe con el tema
        self.lbl_subtitle = lbl_subtitle # Guardamos referencia para cambiarle color
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl_subtitle)
        
        self.layout.addSpacing(10)

        # --- PANEL DE CONEXIÓN ---
        self.frame_login = QFrame()
        layout_login = QVBoxLayout()
        layout_login.setContentsMargins(20, 25, 20, 25)
        layout_login.setSpacing(15)
        self.frame_login.setLayout(layout_login)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre del Alumno (Apellido Nombre)")
        layout_login.addWidget(self.input_name)

        lbl_class = QLabel("Seleccionar Clase:")
        layout_login.addWidget(lbl_class)
        
        self.combo_servers = QComboBox()
        self.combo_servers.addItem("Buscando profesores...")
        layout_login.addWidget(self.combo_servers)
        
        layout_login.addSpacing(10)

        self.btn_connect = QPushButton("Ingresar al Examen")
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.start_exam)
        layout_login.addWidget(self.btn_connect)
        
        self.layout.addWidget(self.frame_login)

        # --- PANEL DE ESTADO ---
        self.lbl_status = QLabel("Esperando conexión...")
        self.lbl_status.setObjectName("Status")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # El color inicial se pone en apply_theme
        self.layout.addWidget(self.lbl_status)
        
        self.layout.addStretch()

        # Iniciar Servicios
        self.discovery = DiscoveryThread()
        self.discovery.server_found.connect(self.add_server)
        self.discovery.start()
        
        self.detected_ips = {}
        self.net_thread = None

        # Aplicar tema inicial
        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(THEME_DARK)
            self.btn_theme.setText("🌙 Modo Noche")
            self.lbl_subtitle.setStyleSheet("color: #bac2de; font-size: 12px;")
            # Ajustar color de status por defecto si no hay mensaje
            if "Esperando" in self.lbl_status.text():
                self.lbl_status.setStyleSheet("color: #6c7086;")
        else:
            self.setStyleSheet(THEME_LIGHT)
            self.btn_theme.setText("☀️ Modo Día")
            self.lbl_subtitle.setStyleSheet("color: #9ca0b0; font-size: 12px;")
            if "Esperando" in self.lbl_status.text():
                self.lbl_status.setStyleSheet("color: #9ca0b0;")
        
        # Re-aplicar estilos específicos de estado si ya hay un mensaje activo
        self.update_status_label(self.lbl_status.text())

    def add_server(self, name, ip):
        if ip not in self.detected_ips:
            if self.combo_servers.count() == 1 and self.combo_servers.itemText(0) == "Buscando profesores...":
                self.combo_servers.clear()
            
            self.detected_ips[ip] = name
            self.combo_servers.addItem(f"{name} ({ip})", ip)

    def start_exam(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Por favor ingresa tu nombre.")
            return
        
        idx = self.combo_servers.currentIndex()
        if idx < 0: return
        server_ip = self.combo_servers.itemData(idx)
        if not server_ip: return

        self.input_name.setDisabled(True)
        self.combo_servers.setDisabled(True)
        self.btn_connect.setText("🔒 EXAMEN EN CURSO")
        self.btn_connect.setObjectName("Locked")
        self.btn_connect.setDisabled(True)
        
        # Truco para forzar la actualización del estilo (por el cambio de ID)
        self.style().unpolish(self.btn_connect)
        self.style().polish(self.btn_connect)

        self.net_thread = NetworkThread(server_ip, name)
        self.net_thread.status_signal.connect(self.update_status_label)
        self.net_thread.start()

    def update_status_label(self, text):
        self.lbl_status.setText(text)
        
        # Definimos colores según el tema
        if self.is_dark_mode:
            c_block = "#f38ba8" # Rojo pastel
            c_safe = "#a6e3a1"  # Verde pastel
            c_wait = "#6c7086"  # Gris
        else:
            c_block = "#d20f39" # Rojo fuerte
            c_safe = "#40a02b"  # Verde fuerte
            c_wait = "#9ca0b0"  # Gris

        if "BLOQUEADO" in text:
            self.lbl_status.setStyleSheet(f"color: {c_block}; font-weight: bold; font-size: 16px;")
        elif "Seguro" in text:
            self.lbl_status.setStyleSheet(f"color: {c_safe}; font-weight: bold; font-size: 16px;")
        else:
            self.lbl_status.setStyleSheet(f"color: {c_wait};")

    def closeEvent(self, event):
        if self.net_thread:
            self.net_thread.running = False
            self.net_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentClient()
    window.show()
    sys.exit(app.exec())