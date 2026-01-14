import sys
import socket
import threading
import json
import time
import base64
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QCheckBox, QFrame, QMessageBox, QAbstractItemView,
                             QTabWidget, QTextEdit, QFileDialog) 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

# --- 1. DEFINICIÓN DE TEMAS ---
THEME_DARK = """
QMainWindow { background-color: #1e1e2e; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #cdd6f4; }
QFrame { background-color: #181825; border-radius: 12px; }
QTableWidget { background-color: #181825; border: 1px solid #313244; gridline-color: #313244; }
QHeaderView::section { background-color: #11111b; padding: 10px; border: none; font-weight: bold; color: #89b4fa; font-size: 15px; }
QTabWidget::pane { border: 1px solid #313244; border-radius: 8px; background-color: #1e1e2e; }
QTabBar::tab { background: #181825; color: #cdd6f4; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #89b4fa; color: #1e1e2e; font-weight: bold; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #b4befe; }
QPushButton#Config { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 8px; }
QPushButton#Config:hover { background-color: #45475a; }
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
QTabWidget::pane { border: 1px solid #dce0e8; border-radius: 8px; background-color: #eff1f5; }
QTabBar::tab { background: #e6e9ef; color: #4c4f69; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
QTabBar::tab:selected { background: #1e66f5; color: #ffffff; font-weight: bold; }
QPushButton { background-color: #1e66f5; color: #ffffff; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #7287fd; }
QPushButton#Config { background-color: #e6e9ef; color: #4c4f69; border: 1px solid #dce0e8; padding: 8px; }
QPushButton#Config:hover { background-color: #dce0e8; }
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
        msg = json.dumps({"type": "CONFIG", "allowed_apps": allowed_list})
        self._broadcast(msg)

    def broadcast_pdf(self, filepath):
        """Lee el PDF, lo convierte a Base64 y lo envía"""
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            # Limite de seguridad: 10MB para no colgar el socket
            if filesize > 10 * 1024 * 1024:
                return False, "El archivo es muy pesado (Max 10MB)"

            with open(filepath, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode('utf-8')

            msg = json.dumps({
                "type": "EXAM_FILE",
                "filename": filename,
                "file_data": encoded_data
            })
            print(f"[SERVIDOR] Enviando PDF: {filename} ({filesize} bytes)")
            self._broadcast(msg)
            return True, "Enviado correctamente"
        except Exception as e:
            return False, str(e)

    def _broadcast(self, json_msg):
        dead_clients = []
        for hostname, sock in self.clients_map.items():
            try:
                sock.sendall(json_msg.encode('utf-8'))
            except:
                dead_clients.append(hostname)
        for h in dead_clients:
            self.clients_map.pop(h, None)

    def send_private_config(self, target_hostname, allowed_list):
        sock = self.clients_map.get(target_hostname)
        if sock:
            msg = json.dumps({"type": "CONFIG", "allowed_apps": allowed_list})
            try:
                sock.sendall(msg.encode('utf-8'))
                return True
            except: return False
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
        self.selected_pdf_path = None
        
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

        # 2. CONTENIDO PRINCIPAL
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        global_layout.addLayout(content_layout)

        # A. PANEL LATERAL
        side_panel = QFrame()
        side_panel.setFixedWidth(280)
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(20, 25, 20, 25)
        side_layout.setSpacing(15)
        side_panel.setLayout(side_layout)
        
        lbl_control = QLabel("Controles")
        lbl_control.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        side_layout.addWidget(lbl_control)
        side_layout.addSpacing(5)
        
        lbl_wb = QLabel("🔓 Permitir Apps:")
        side_layout.addWidget(lbl_wb)
        self.chk_chrome = QCheckBox("Navegador Web")
        self.chk_discord = QCheckBox("Discord")
        self.chk_calc = QCheckBox("Calculadora")
        side_layout.addWidget(self.chk_chrome)
        side_layout.addWidget(self.chk_discord)
        side_layout.addWidget(self.chk_calc)
        side_layout.addSpacing(15)
        
        self.btn_apply = QPushButton("Aplicar a TODOS")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.clicked.connect(self.broadcast_rules)
        side_layout.addWidget(self.btn_apply)

        self.btn_apply_single = QPushButton("Aplicar a Selección")
        self.btn_apply_single.setObjectName("SingleUser")
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

        # B. TABS
        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)

        # TAB 1: MONITOR
        self.tab_monitor = QWidget()
        tab_mon_layout = QVBoxLayout()
        self.tab_monitor.setLayout(tab_mon_layout)
        
        lbl_table = QLabel("Estado de Alumnos")
        lbl_table.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        tab_mon_layout.addWidget(lbl_table)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Alumno", "IP", "Estado Actual"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tab_mon_layout.addWidget(self.table)
        self.tabs.addTab(self.tab_monitor, "📡 Monitor")

        # TAB 2: PDF (CONSIGNA)
        self.tab_exam = QWidget()
        tab_exam_layout = QVBoxLayout()
        tab_exam_layout.setContentsMargins(40, 40, 40, 40)
        tab_exam_layout.setSpacing(20)
        self.tab_exam.setLayout(tab_exam_layout)
        
        lbl_exam_title = QLabel("Cargar Archivo de Examen (PDF)")
        lbl_exam_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_exam_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tab_exam_layout.addWidget(lbl_exam_title)

        # Zona de carga
        self.lbl_file_status = QLabel("Ningún archivo seleccionado")
        self.lbl_file_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_file_status.setStyleSheet("color: #6c7086; font-size: 14px;")
        tab_exam_layout.addWidget(self.lbl_file_status)

        btn_select_file = QPushButton("📂 Seleccionar PDF")
        btn_select_file.setFixedSize(200, 50)
        btn_select_file.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_file.clicked.connect(self.select_pdf)
        
        # Centramos el botón
        h_layout_btn = QHBoxLayout()
        h_layout_btn.addStretch()
        h_layout_btn.addWidget(btn_select_file)
        h_layout_btn.addStretch()
        tab_exam_layout.addLayout(h_layout_btn)

        tab_exam_layout.addSpacing(20)
        
        self.btn_send_pdf = QPushButton("📤 ENVIAR PDF A ALUMNOS")
        self.btn_send_pdf.setFixedHeight(60)
        self.btn_send_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_pdf.setEnabled(False) # Deshabilitado hasta que seleccione algo
        self.btn_send_pdf.setStyleSheet("background-color: #313244; color: #6c7086;") # Estilo deshabilitado
        self.btn_send_pdf.clicked.connect(self.send_pdf_broadcast)
        tab_exam_layout.addWidget(self.btn_send_pdf)
        
        tab_exam_layout.addStretch()

        self.tabs.addTab(self.tab_exam, "📝 Consigna PDF")
        
        self.tab_chat = QWidget()
        self.tabs.addTab(self.tab_chat, "💬 Chat")

        self.apply_theme()

    def select_pdf(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Abrir Archivo de Examen', '.', "PDF Files (*.pdf)")
        if fname:
            self.selected_pdf_path = fname
            filename = os.path.basename(fname)
            self.lbl_file_status.setText(f"✅ Archivo listo: {filename}")
            self.lbl_file_status.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 16px;")
            
            # Habilitar botón de enviar
            self.btn_send_pdf.setEnabled(True)
            self.btn_send_pdf.setText(f"📤 ENVIAR '{filename}' AHORA")
            self.btn_send_pdf.setStyleSheet("background-color: #fab387; color: #1e1e2e; font-size: 16px; font-weight: bold;")

    def send_pdf_broadcast(self):
        if not self.selected_pdf_path: return
        
        confirm = QMessageBox.question(self, "Confirmar Envío", 
                                       "¿Estás seguro de enviar este archivo a TODOS los alumnos conectados?\n\nSe abrirá automáticamente en sus pantallas.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = self.server_thread.broadcast_pdf(self.selected_pdf_path)
            if success:
                QMessageBox.information(self, "Éxito", "El archivo se ha enviado correctamente.")
            else:
                QMessageBox.critical(self, "Error", f"Fallo el envío: {msg}")

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
            if item: self.update_row_color(row, item.text())

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
            c = {"ok": "#a6e3a1", "alert": "#f38ba8", "disc": "#6c7086"}
        else:
            c = {"ok": "#40a02b", "alert": "#d20f39", "disc": "#9ca0b0"}

        if "ALERT" in status: color = c["alert"]
        elif "Desconectado" in status: color = c["disc"]
        else: color = c["ok"]

        item = QTableWidgetItem(status)
        item.setForeground(QColor(color))
        item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.table.setItem(row, 2, item)

    def broadcast_rules(self):
        allowed = []
        if self.chk_chrome.isChecked(): allowed.extend(["chrome.exe", "msedge.exe"])
        if self.chk_discord.isChecked(): allowed.append("discord.exe")
        if self.chk_calc.isChecked(): allowed.append("calculatorapp.exe")
        
        self.server_thread.broadcast_config(allowed)
        self.btn_apply.setText("¡Enviado!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.btn_apply.setText("Aplicar a TODOS"))

    def apply_to_selection(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.warning(self, "Atención", "Selecciona un alumno.")
            return
        target = sel[0].text()
        
        allowed = []
        if self.chk_chrome.isChecked(): allowed.extend(["chrome.exe", "msedge.exe"])
        if self.chk_discord.isChecked(): allowed.append("discord.exe")
        if self.chk_calc.isChecked(): allowed.append("calculatorapp.exe")

        if self.server_thread.send_private_config(target, allowed):
            QMessageBox.information(self, "Éxito", f"Reglas aplicadas a {target}")
        else:
            QMessageBox.critical(self, "Error", "No se pudo conectar.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TeacherDashboard()
    window.show()
    sys.exit(app.exec())