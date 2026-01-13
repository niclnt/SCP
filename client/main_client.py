import sys
import socket
import threading
import json
import time
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame, QTextEdit)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QFont, QIcon

# IMPORTANTE: Asegúrate de tener estas líneas para las rutas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from security import guard

# --- TEMAS (Incluye estilos para la ventana de examen) ---
THEME_DARK = """
QWidget { background-color: #1e1e2e; font-family: 'Segoe UI', sans-serif; color: #cdd6f4; }
QLineEdit, QTextEdit { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 10px; color: white; font-size: 14px; }
QComboBox { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 10px; color: white; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border-radius: 8px; padding: 12px; font-weight: bold; }
QPushButton:hover { background-color: #b4befe; }
QPushButton#Locked { background-color: #f38ba8; color: #181825; }
QPushButton#Config { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 8px; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #fab387; }
QFrame { background-color: #181825; border-radius: 12px; }
"""

THEME_LIGHT = """
QWidget { background-color: #eff1f5; font-family: 'Segoe UI', sans-serif; color: #4c4f69; }
QLineEdit, QTextEdit { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 10px; color: #4c4f69; }
QComboBox { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 10px; color: #4c4f69; }
QPushButton { background-color: #1e66f5; color: #ffffff; border-radius: 8px; padding: 12px; font-weight: bold; }
QPushButton:hover { background-color: #7287fd; }
QPushButton#Locked { background-color: #d20f39; color: #ffffff; }
QPushButton#Config { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #dce0e8; padding: 8px; }
QLabel#Title { font-size: 22px; font-weight: bold; color: #fe640b; }
QFrame { background-color: #e6e9ef; border-radius: 12px; border: 1px solid #dce0e8; }
"""

# --- NUEVA VENTANA DE EXAMEN ---
class ExamWindow(QWidget):
    def __init__(self, title, content, is_dark):
        super().__init__()
        self.setWindowTitle(f"CONSIGNA: {title}")
        self.resize(600, 700)
        
        # Aplicamos tema según lo que tenga el alumno
        self.setStyleSheet(THEME_DARK if is_dark else THEME_LIGHT)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl_head = QLabel(title)
        lbl_head.setObjectName("Title")
        lbl_head.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_head)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True) # El alumno solo lee
        self.text_area.setPlainText(content)
        # Fuente un poco más grande para leer fácil
        self.text_area.setFont(QFont("Segoe UI", 12)) 
        layout.addWidget(self.text_area)

        btn_close = QPushButton("Entendido / Cerrar")
        btn_close.clicked.connect(self.hide)
        layout.addWidget(btn_close)

# --- RED ---
class DiscoveryThread(QThread):
    server_found = pyqtSignal(str, str) 

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(('', 5555))
        except: return 
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get('type') == 'SCP_SERVER':
                    self.server_found.emit(msg['name'], msg['ip'])
            except: pass

class NetworkThread(QThread):
    status_signal = pyqtSignal(str)
    exam_signal = pyqtSignal(str, str) # Nueva señal para abrir ventana de examen

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
                if guard.sabotage_ai_extensions():
                    guard.kill_vscode_processes()

                process_violations = guard.get_running_violations()
                if process_violations:
                    for proc in process_violations: guard.kill_specific_process(proc)

                folder_violations = guard.check_settings_violations()
                all_violations = folder_violations + process_violations

                if all_violations:
                    msg = json.dumps({"type": "ALERT", "violations": all_violations})
                    self.status_signal.emit(f"⚠️ BLOQUEADO: {all_violations[0]}")
                else:
                    msg = json.dumps({"type": "STATUS", "status": "CLEAN"})
                    self.status_signal.emit("✅ Examen Seguro - Monitoreando")

                try: self.sock.sendall(msg.encode('utf-8'))
                except: break 
                time.sleep(2)

        except Exception as e:
            self.status_signal.emit(f"Error: {e}")
        finally:
            self.running = False
            if self.sock: self.sock.close()

    def receive_loop(self):
        try:
            while self.running:
                data = self.sock.recv(4096) # Buffer grande por si el examen es largo
                if not data: break
                
                # A veces llegan mensajes pegados. Esto es básico, para texto muy largo se requiere un protocolo mejor
                # pero para este MVP funcionará con textos razonables.
                try:
                    msg = json.loads(data.decode('utf-8'))
                    
                    if msg.get('type') == 'CONFIG':
                        allowed = msg.get('allowed_apps', [])
                        guard.update_config(allowed)
                    
                    elif msg.get('type') == 'EXAM_CONTENT':
                        # DISPARAMOS LA SEÑAL A LA UI
                        title = msg.get('title', 'Examen')
                        content = msg.get('content', '')
                        self.exam_signal.emit(title, content)
                except: pass     
        except: pass

# --- UI CLIENTE ---
class StudentClient(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Examen Seguro")
        self.resize(400, 550)
        self.is_dark_mode = True 
        
        # Referencia a la ventana de examen para que no se borre de memoria
        self.exam_window = None

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(15)
        self.setLayout(self.layout)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_theme = QPushButton("⚙️ Tema Oscuro")
        self.btn_theme.setObjectName("Config")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_theme.setFixedWidth(150)
        top_bar.addWidget(self.btn_theme)
        self.layout.addLayout(top_bar)

        # Header
        lbl_title = QLabel("SCP ExamGuard")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(lbl_title)
        
        self.lbl_subtitle = QLabel("Sistema de Control de Procesos")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_subtitle)
        self.layout.addSpacing(10)

        # Login Frame
        self.frame_login = QFrame()
        layout_login = QVBoxLayout()
        layout_login.setContentsMargins(20, 25, 20, 25)
        layout_login.setSpacing(15)
        self.frame_login.setLayout(layout_login)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nombre del Alumno")
        layout_login.addWidget(self.input_name)
        layout_login.addWidget(QLabel("Seleccionar Clase:"))
        self.combo_servers = QComboBox()
        self.combo_servers.addItem("Buscando profesores...")
        layout_login.addWidget(self.combo_servers)
        layout_login.addSpacing(10)

        self.btn_connect = QPushButton("Ingresar al Examen")
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_connect.clicked.connect(self.start_exam)
        layout_login.addWidget(self.btn_connect)
        self.layout.addWidget(self.frame_login)

        # Status
        self.lbl_status = QLabel("Esperando conexión...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_status)
        self.layout.addStretch()

        # Threads
        self.discovery = DiscoveryThread()
        self.discovery.server_found.connect(self.add_server)
        self.discovery.start()
        self.detected_ips = {}
        self.net_thread = None

        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        if self.exam_window and self.exam_window.isVisible():
            self.exam_window.setStyleSheet(THEME_DARK if self.is_dark_mode else THEME_LIGHT)

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(THEME_DARK)
            self.btn_theme.setText("🌙 Modo Noche")
            self.lbl_subtitle.setStyleSheet("color: #bac2de; font-size: 12px;")
            if "Esperando" in self.lbl_status.text(): self.lbl_status.setStyleSheet("color: #6c7086;")
        else:
            self.setStyleSheet(THEME_LIGHT)
            self.btn_theme.setText("☀️ Modo Día")
            self.lbl_subtitle.setStyleSheet("color: #9ca0b0; font-size: 12px;")
            if "Esperando" in self.lbl_status.text(): self.lbl_status.setStyleSheet("color: #9ca0b0;")
        self.update_status_label(self.lbl_status.text())

    def add_server(self, name, ip):
        if ip not in self.detected_ips:
            if self.combo_servers.count() == 1 and self.combo_servers.itemText(0) == "Buscando profesores...":
                self.combo_servers.clear()
            self.detected_ips[ip] = name
            self.combo_servers.addItem(f"{name} ({ip})", ip)

    def start_exam(self):
        name = self.input_name.text().strip()
        if not name: return
        idx = self.combo_servers.currentIndex()
        if idx < 0: return
        server_ip = self.combo_servers.itemData(idx)
        if not server_ip: return

        self.input_name.setDisabled(True)
        self.combo_servers.setDisabled(True)
        self.btn_connect.setText("🔒 EXAMEN EN CURSO")
        self.btn_connect.setObjectName("Locked")
        self.btn_connect.setDisabled(True)
        self.style().unpolish(self.btn_connect)
        self.style().polish(self.btn_connect)

        self.net_thread = NetworkThread(server_ip, name)
        self.net_thread.status_signal.connect(self.update_status_label)
        
        # CONECTAMOS LA SEÑAL DE EXAMEN A LA FUNCION QUE ABRE LA VENTANA
        self.net_thread.exam_signal.connect(self.show_exam_popup)
        
        self.net_thread.start()

    def show_exam_popup(self, title, content):
        """Abre la ventana flotante con la consigna"""
        self.exam_window = ExamWindow(title, content, self.is_dark_mode)
        self.exam_window.show()

    def update_status_label(self, text):
        self.lbl_status.setText(text)
        if self.is_dark_mode: c = {"block": "#f38ba8", "safe": "#a6e3a1", "wait": "#6c7086"}
        else: c = {"block": "#d20f39", "safe": "#40a02b", "wait": "#9ca0b0"}

        if "BLOQUEADO" in text: color = c["block"]
        elif "Seguro" in text: color = c["safe"]
        else: color = c["wait"]
        
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")

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