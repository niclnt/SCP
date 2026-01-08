import sys
import socket
import threading
import json
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QCheckBox, QFrame, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

# --- 1. DEFINICIÓN DE TEMAS ---
THEME_DARK = """
QMainWindow { background-color: #1e1e2e; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #cdd6f4; }
QFrame { background-color: #181825; border-radius: 12px; }
QTableWidget { background-color: #181825; border: 1px solid #313244; gridline-color: #313244; }
QHeaderView::section { background-color: #11111b; padding: 10px; border: none; font-weight: bold; color: #89b4fa; font-size: 15px; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #b4befe; }
QPushButton#Config { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 8px; }
QPushButton#Config:hover { background-color: #45475a; }
/* Estilo para el botón secundario (Aplicar a uno solo) */
QPushButton#SingleUser { background-color: #fab387; color: #1e1e2e; }
QPushButton#SingleUser:hover { background-color: #f9e2af; }
QCheckBox { spacing: 8px; color: #cdd6f4; }
QCheckBox::indicator { width: 20px; height: 20px; border-radius: 6px; border: 1px solid #585b70; }
QCheckBox::indicator:checked { background-color: #a6e3a1; border: 1px solid #a6e3a1; }
QLabel#Title { font-size: 20px; font-weight: bold; color: #fab387; }
QLabel#SubInfo { color: #6c7086; font-size: 12px; }
"""

THEME_LIGHT = """
QMainWindow { background-color: #eff1f5; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #4c4f69; }
QFrame { background-color: #e6e9ef; border-radius: 12px; border: 1px solid #dce0e8; }
QTableWidget { background-color: #ffffff; border: 1px solid #ccd0da; gridline-color: #ccd0da; }
QHeaderView::section { background-color: #dce0e8; padding: 10px; border: none; font-weight: bold; color: #1e66f5; font-size: 15px; }
QPushButton { background-color: #1e66f5; color: #ffffff; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #7287fd; }
QPushButton#Config { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #dce0e8; padding: 8px; }
QPushButton#Config:hover { background-color: #dce0e8; }
/* Estilo para el botón secundario */
QPushButton#SingleUser { background-color: #fe640b; color: #ffffff; }
QPushButton#SingleUser:hover { background-color: #ff9d6e; }
QCheckBox { spacing: 8px; color: #4c4f69; }
QCheckBox::indicator { width: 20px; height: 20px; border-radius: 6px; border: 1px solid #9ca0b0; background-color: white; }
QCheckBox::indicator:checked { background-color: #40a02b; border: 1px solid #40a02b; }
QLabel#Title { font-size: 20px; font-weight: bold; color: #fe640b; }
QLabel#SubInfo { color: #9ca0b0; font-size: 12px; }
"""

# --- UTILIDADES ---
def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class BroadcastSender(threading.Thread):
    def __init__(self, port=5555): 
        super().__init__()
        self.port = port
        self.running = True
        self.host_name = socket.gethostname()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.running:
            try:
                real_ip = get_lan_ip()
                message = json.dumps({
                    "name": f"Clase de {self.host_name}",
                    "type": "SCP_SERVER",
                    "ip": real_ip
                })
                sock.sendto(message.encode('utf-8'), ('<broadcast>', self.port))
                time.sleep(2) 
            except Exception:
                time.sleep(5)

class ServerThread(threading.Thread):
    def __init__(self, port, callback):
        super().__init__()
        self.port = port
        self.update_callback = callback
        self.server_socket = None
        self.running = True
        
        # CAMBIO IMPORTANTE: Ahora es un diccionario { "NombreAlumno": Socket }
        # Esto nos permite buscar el socket de alguien específico.
        self.clients_map = {} 

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(10)
        print(f"Servidor escuchando en puerto {self.port}")

        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()
            except: break

    def broadcast_config(self, allowed_list):
        """Envía reglas a TODOS"""
        msg = json.dumps({"type": "CONFIG", "allowed_apps": allowed_list})
        print(f"[SERVIDOR] Broadcast rules: {allowed_list}")
        
        # Iteramos sobre los valores (los sockets) del diccionario
        dead_clients = []
        for hostname, sock in self.clients_map.items():
            try:
                sock.sendall(msg.encode('utf-8'))
            except:
                dead_clients.append(hostname)
        
        # Limpieza
        for h in dead_clients:
            self.clients_map.pop(h, None)

    def send_private_config(self, target_hostname, allowed_list):
        """Envía reglas a UN SOLO alumno"""
        sock = self.clients_map.get(target_hostname)
        if sock:
            msg = json.dumps({"type": "CONFIG", "allowed_apps": allowed_list})
            try:
                sock.sendall(msg.encode('utf-8'))
                print(f"[SERVIDOR] Reglas privadas enviadas a {target_hostname}")
                return True
            except:
                return False
        return False

    def handle_client(self, client_sock, addr):
        ip = addr[0]
        hostname = "Desconocido"
        try:
            while True:
                data = client_sock.recv(4096)
                if not data: break
                msg = json.loads(data.decode('utf-8'))
                
                if msg['type'] == 'REGISTER':
                    hostname = msg['hostname']
                    # REGISTRAMOS AL ALUMNO EN EL DICCIONARIO
                    self.clients_map[hostname] = client_sock
                    self.update_callback(hostname, ip, "🟢 Conectado")
                
                elif msg['type'] == 'ALERT':
                    violations = ", ".join(msg['violations'])
                    self.update_callback(hostname, ip, f"🔴 ALERT: {violations}")
                
                elif msg['type'] == 'STATUS' and msg.get('status') == 'CLEAN':
                    self.update_callback(hostname, ip, "🟢 Seguro")
        except: pass
        finally:
            self.update_callback(hostname, ip, "⚪ Desconectado")
            # Si se desconecta, lo borramos del mapa
            if hostname in self.clients_map:
                del self.clients_map[hostname]
            client_sock.close()

# --- INTERFAZ GRÁFICA ---
class TeacherDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCP - Monitor Docente Pro")
        self.resize(1150, 750)
        self.is_dark_mode = True 
        
        self.broadcaster = BroadcastSender()
        self.broadcaster.daemon = True 
        self.broadcaster.start()

        self.server_thread = ServerThread(9999, self.update_row)
        self.server_thread.daemon = True
        self.server_thread.start()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        global_layout = QVBoxLayout()
        global_layout.setContentsMargins(20, 20, 20, 20)
        global_layout.setSpacing(15)
        main_widget.setLayout(global_layout)

        # 1. TOP BAR
        top_bar = QHBoxLayout()
        lbl_main_title = QLabel("SCP Monitor")
        lbl_main_title.setObjectName("Title")
        top_bar.addWidget(lbl_main_title)
        top_bar.addStretch() 
        self.btn_theme = QPushButton("⚙️ Tema Oscuro")
        self.btn_theme.setObjectName("Config")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setFixedWidth(150)
        self.btn_theme.clicked.connect(self.toggle_theme)
        top_bar.addWidget(self.btn_theme)
        global_layout.addLayout(top_bar)

        # 2. CONTENIDO
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        global_layout.addLayout(content_layout)

        # A. PANEL LATERAL
        side_panel = QFrame()
        side_panel.setFixedWidth(300)
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(25, 30, 25, 30)
        side_layout.setSpacing(15)
        side_panel.setLayout(side_layout)
        
        lbl_control = QLabel("Controles de Examen")
        lbl_control.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        side_layout.addWidget(lbl_control)
        side_layout.addSpacing(10)
        
        lbl_wb = QLabel("🔓 Permitir Aplicaciones:")
        side_layout.addWidget(lbl_wb)

        self.chk_chrome = QCheckBox("Navegador Web")
        self.chk_discord = QCheckBox("Discord / Chat")
        self.chk_calc = QCheckBox("Calculadora")
        
        side_layout.addWidget(self.chk_chrome)
        side_layout.addWidget(self.chk_discord)
        side_layout.addWidget(self.chk_calc)
        
        side_layout.addSpacing(20)
        
        # BOTÓN 1: GLOBAL
        self.btn_apply = QPushButton("Aplicar a TODOS")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.clicked.connect(self.broadcast_rules)
        side_layout.addWidget(self.btn_apply)

        # BOTÓN 2: INDIVIDUAL (NUEVO)
        self.btn_apply_single = QPushButton("Aplicar SOLO a Selección")
        self.btn_apply_single.setObjectName("SingleUser") # ID para estilo Naranja
        self.btn_apply_single.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply_single.clicked.connect(self.apply_to_selection)
        side_layout.addWidget(self.btn_apply_single)
        
        side_layout.addStretch()
        
        real_ip = get_lan_ip()
        self.lbl_info = QLabel(f"IP Servidor:\n{real_ip}")
        self.lbl_info.setObjectName("SubInfo")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.lbl_info)

        content_layout.addWidget(side_panel)

        # B. TABLA CENTRAL
        table_layout = QVBoxLayout()
        lbl_table = QLabel("Estado de Alumnos (Selecciona para acciones individuales)")
        lbl_table.setStyleSheet("font-weight: bold; font-size: 14px; color: #89b4fa;")
        table_layout.addWidget(lbl_table)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Alumno", "IP", "Estado Actual"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        
        # Permitir seleccionar filas enteras, pero solo una a la vez
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        table_layout.addWidget(self.table)

        content_layout.addLayout(table_layout)
        self.apply_theme()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(THEME_DARK)
            self.btn_theme.setText("🌙 Modo Noche")
        else:
            self.setStyleSheet(THEME_LIGHT)
            self.btn_theme.setText("☀️ Modo Día")
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            if item:
                self.update_row_color(row, item.text())

    def update_row(self, hostname, ip, status):
        found_row = -1
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == hostname:
                found_row = row
                break
        
        if found_row == -1:
            found_row = self.table.rowCount()
            self.table.insertRow(found_row)
            self.table.setItem(found_row, 0, QTableWidgetItem(hostname))
            self.table.setItem(found_row, 1, QTableWidgetItem(ip))
            self.table.setItem(found_row, 2, QTableWidgetItem(""))

        self.update_row_color(found_row, status)

    def update_row_color(self, row, status):
        if self.is_dark_mode:
            color_ok = "#a6e3a1"
            color_alert = "#f38ba8"
            color_disc = "#6c7086"
        else:
            color_ok = "#40a02b"
            color_alert = "#d20f39"
            color_disc = "#9ca0b0"

        if "ALERT" in status:
            final_color = color_alert
        elif "Desconectado" in status:
            final_color = color_disc
        else:
            final_color = color_ok

        item = QTableWidgetItem(status)
        item.setForeground(QColor(final_color))
        item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.table.setItem(row, 2, item)

    def get_rules_from_checkboxes(self):
        """Helper para obtener la lista de checkboxes"""
        allowed = []
        if self.chk_chrome.isChecked(): allowed.extend(["chrome.exe", "msedge.exe"])
        if self.chk_discord.isChecked(): allowed.append("discord.exe")
        if self.chk_calc.isChecked(): allowed.append("calculatorapp.exe")
        return allowed

    def broadcast_rules(self):
        allowed = self.get_rules_from_checkboxes()
        self.server_thread.broadcast_config(allowed)
        
        original_text = self.btn_apply.text()
        self.btn_apply.setText("¡Enviado a TODOS!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_apply.setText(original_text))

    def apply_to_selection(self):
        # 1. Obtener la fila seleccionada
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Atención", "Selecciona primero un alumno de la lista.")
            return
        
        # Como seleccionamos filas enteras, el primer item es el nombre (columna 0)
        target_name = selected_items[0].text()
        
        # 2. Obtener reglas
        allowed = self.get_rules_from_checkboxes()
        
        # 3. Enviar mensaje privado
        success = self.server_thread.send_private_config(target_name, allowed)
        
        if success:
            QMessageBox.information(self, "Éxito", f"Reglas aplicadas SOLO a: {target_name}")
        else:
            QMessageBox.critical(self, "Error", f"No se pudo enviar a {target_name}. Quizás se desconectó.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeacherDashboard()
    window.show()
    sys.exit(app.exec())